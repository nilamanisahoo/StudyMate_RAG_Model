
import json
from pathlib import Path
from time import sleep

from langchain_core.documents import Document

from backend.app.ingestion.pdf_renderer import render_pdf_pages
from backend.app.services.vision_service import analyze_page_image


def get_visual_cache_path() -> Path:
    """Return the path of the local visual-description cache."""
    project_root = Path(__file__).resolve().parents[3]
    cache_directory = project_root / ".cache"
    cache_directory.mkdir(parents=True, exist_ok=True)

    return cache_directory / "visual_page_cache.json"


def load_visual_cache() -> dict:
    """Load previously saved visual descriptions."""
    cache_path = get_visual_cache_path()

    if not cache_path.exists():
        return {}

    try:
        with cache_path.open("r", encoding="utf-8") as file:
            cache = json.load(file)

        if isinstance(cache, dict):
            return cache

        return {}

    except (json.JSONDecodeError, OSError) as error:
        print(f"Could not load visual cache: {error}")
        return {}


def save_visual_cache(cache: dict) -> None:
    """Save visual descriptions so future runs can reuse them."""
    cache_path = get_visual_cache_path()

    with cache_path.open("w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=2)


def is_non_retryable_gemini_error(error: Exception) -> bool:
    """Identify Gemini errors that should stop further page analysis."""

    error_text = str(error).lower()
    status_code = getattr(error, "code", None)

    # Stop if the service reports a budget or quota-related error.
    budget_or_quota_errors = (
        "in_flight_budget_exhausted",
        "openrouter_in_flight_budget",
        "resource_exhausted",
        "quota_exceeded",
        "billing",
    )

    if any(message in error_text for message in budget_or_quota_errors):
        return True

    # Do not repeatedly retry permanent request or account errors.
    return status_code in {400, 401, 402, 403, 404}

def analyze_all_pdf_pages(
    pdf_content: bytes,
    source: str,
    user_id: str,
    pdf_hash: str,
    dpi: int = 150,
    max_attempts: int = 3,
    page_numbers: list[int] | None = None,
) -> tuple[list[Document], list[int]]:
    """
    Analyze PDF pages and return:
    1. Documents containing visual descriptions.
    2. Page numbers that could not be analyzed.

    Successful descriptions are cached locally.
    """

    # Step 1: Validate inputs.
    if not pdf_content:
        raise ValueError("PDF content can't be empty.")

    if not source.strip():
        raise ValueError("Source filename cannot be empty.")

    if not user_id.strip():
        raise ValueError("user_id cannot be empty.")

    if not pdf_hash.strip():
        raise ValueError("pdf_hash cannot be empty.")

    if dpi < 1:
        raise ValueError("dpi must be greater than 0.")

    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    # Step 2: Render the requested PDF pages as images.
    rendered_pages = render_pdf_pages(
        pdf_content=pdf_content,
        page_numbers=page_numbers,
        dpi=dpi,
    )

    # Step 3: Load the cache and prepare result lists.
    visual_cache = load_visual_cache()
    successful_documents = []
    failed_pages = []
    cache_hits = 0

    # Step 4: Process each rendered page.
    for page_index, rendered_page in enumerate(rendered_pages):
        page_number = rendered_page["page"]
        image_bytes = rendered_page["image"]

        # Create a unique cache key for this user's PDF and page.
        cache_key = (
            f"{user_id}:{pdf_hash}:{page_number}:{dpi}"
        )

        description = visual_cache.get(cache_key)

        # Step 5: Reuse the description if it is already cached.
        if isinstance(description, str) and description.strip():
            cache_hits += 1

            print(
                f"Using cached visual description "
                f"for page {page_number}."
            )

        else:
            description = None
            budget_limit_reached = False

            # Step 6: Ask the vision model to analyze the page.
            for attempt in range(1, max_attempts + 1):
                try:
                    result = analyze_page_image(
                        image_bytes=image_bytes,
                        source=source,
                        page_number=page_number,
                    )

                    if (
                        not isinstance(result, str)
                        or not result.strip()
                    ):
                        raise ValueError(
                            "The vision model returned "
                            "an empty description."
                        )

                    description = result.strip()
                    break

                except Exception as error:
                    print(
                        f"Vision analysis failed for page "
                        f"{page_number}, attempt "
                        f"{attempt}/{max_attempts}: {error}"
                    )

                    # Stop immediately for this specific budget error.
                    if is_non_retryable_gemini_error(error):
                        print(
                            "A non-retryable Gemini error occurred. "
                            "Stopping further visual analysis."
                        )

                        budget_limit_reached = True
                        break

                    # Retry other errors with increasing delays.
                    if attempt < max_attempts:
                        sleep(min(2 ** (attempt - 1), 8))

            # Step 7: Stop processing remaining pages if the
            # OpenRouter budget limit was reached.
            if budget_limit_reached:
                failed_pages.extend(
                    page["page"]
                    for page in rendered_pages[page_index:]
                )
                break

            # Step 8: Record a page that failed all attempts.
            if not isinstance(description, str) or not description.strip():
                failed_pages.append(page_number)
                continue

            # Step 9: Save each successful description immediately.
            visual_cache[cache_key] = description

            try:
                save_visual_cache(visual_cache)
                print(
                    f"Saved visual description "
                    f"for page {page_number} to cache."
                )
            except OSError as error:
                print(
                    f"Could not save visual cache "
                    f"for page {page_number}: {error}"
                )

        # Step 10: Create a LangChain Document for this page.
        successful_documents.append(
            Document(
                page_content=(
                    f"Visual analysis of PDF '{source}', "
                    f"page {page_number}:\n{description}"
                ),
                metadata={
                    "source": source,
                    "pdf_hash": pdf_hash,
                    "user_id": user_id,
                    "page": page_number,
                    "chunk": 1,
                    "content_type": "visual",
                },
            )
        )

    # Step 11: Report the cache results.
    print(f"Visual cache hits: {cache_hits}")
    print(f"Successful visual descriptions: {len(successful_documents)}")
    print(f"Failed pages: {failed_pages}")

    return successful_documents, failed_pages
