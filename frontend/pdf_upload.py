
import hashlib
import requests
import streamlit as st

from api_client import API_URL, get_api_headers


def render_pdf_upload():
    """Display the PDF uploader and process uploaded PDFs."""

    st.subheader("Upload your PDF")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        max_upload_size=20,
    )

    if uploaded_file is None:
        return

    access_token = st.session_state.get("access_token")

    if not access_token:
        st.error(
            "Your login session has expired. Please log in again."
        )
        return

    # -----------------------------------------
    # Identify the uploaded PDF
    # -----------------------------------------

    pdf_content = uploaded_file.getvalue()

    pdf_hash = hashlib.sha256(pdf_content).hexdigest()

    if "uploaded_pdf_hash" not in st.session_state:
        st.session_state["uploaded_pdf_hash"] = None

    # -----------------------------------------
    # Avoid uploading the same PDF again
    # -----------------------------------------

    if st.session_state["uploaded_pdf_hash"] == pdf_hash:

        st.success(
            f"{uploaded_file.name} is already uploaded "
            "in this session."
        )
        return

    # -----------------------------------------
    # Upload and process PDF
    # -----------------------------------------

    try:
        with st.spinner(
            "Uploading and processing your PDF. "
            "Creating embeddings and saving to Supabase..."
        ):

            response = requests.post(
                f"{API_URL}/upload",
                headers=get_api_headers(),
                files={
                    "file": (
                        uploaded_file.name,
                        pdf_content,
                        "application/pdf",
                    )
                },
                timeout=(10, 600),
            )

        if response.status_code == 401:

            st.error(
                "Your login session has expired. "
                "Please log out and log in again."
            )
            return

        response.raise_for_status()

        result = response.json()

        # Save the hash only after successful processing.
        st.session_state["uploaded_pdf_hash"] = pdf_hash

        st.success(
            f"Successfully processed {result['filename']}!"
        )

        st.write(
            "Documents saved:",
            result["total_documents"],
        )

        if result.get("failed_visual_pages"):

            st.warning(
                "Visual analysis could not process pages: "
                f"{result['failed_visual_pages']}"
            )

    except requests.exceptions.ConnectionError:

        st.error(
            "Cannot connect to FastAPI. "
            "Please start the backend."
        )

    except requests.exceptions.Timeout:

        st.error(
            "PDF processing took too long. "
            "Please try again."
        )

    except requests.exceptions.HTTPError:

        try:
            error_detail = response.json().get(
                "detail",
                "PDF processing failed.",
            )

        except ValueError:
            error_detail = "PDF processing failed."

        st.error(f"Upload failed: {error_detail}")

    except ValueError:

        st.error(
            "The API returned an invalid response."
        )

    except KeyError as error:

        st.error(
            f"The API response is missing a required field: {error}"
        )
