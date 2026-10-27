
from ..retrieval.retriever import create_hybrid_retriever
from ..reranking.reranker import get_reranker


def debug_retrieval(
    query: str,
    user_id: str,
    k: int = 4,
) -> None:
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not user_id:
        raise ValueError("user_id is required.")

    if k < 1:
        raise ValueError("k must be at least 1.")

    retriever = create_hybrid_retriever(
        user_id=user_id,
        k=k,
    )

    candidates = retriever.invoke(query)

    if not candidates:
        print("No candidate chunks were retrieved.")
        return

    reranker = get_reranker()

    pairs = [
        (query, document.page_content)
        for document in candidates
    ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(candidates, scores),
        key=lambda item: float(item[1]),
        reverse=True,
    )

    # Experimental thresholds for comparison only.
    thresholds = [-2.0, -1.0, 0.0, 1.0, 2.0]

    print(f"\nQuestion: {query}")
    print(f"Retrieved candidates: {len(ranked)}")

    print("\n--- Threshold comparison ---")

    for threshold in thresholds:
        kept = [
            (document, float(score))
            for document, score in ranked
            if float(score) >= threshold
        ]

        print(
            f"Threshold {threshold:>5.1f}: "
            f"{len(kept)} passages qualify; "
            f"top {k} limit keeps {min(len(kept), k)}"
        )

    print("\n--- All candidates, ranked by score ---")

    for rank, (document, score) in enumerate(
        ranked,
        start=1,
    ):
        score = float(score)
        source = document.metadata.get("source", "Unknown PDF")
        page = document.metadata.get("page", "Unknown")

        print(f"\nRank: {rank} | Score: {score:.4f}")
        print(f"Source: {source} | Page: {page}")
        print(document.page_content[:500])

    print("\n--- Current production filter: min_score = 0.0 ---")

    current_kept = [
        (document, float(score))
        for document, score in ranked
        if float(score) >= 0.0
    ][:k]

    if not current_kept:
        print("No passages qualify under the current threshold.")
    else:
        for rank, (document, score) in enumerate(
            current_kept,
            start=1,
        ):
            print(
                f"{rank}. Score: {score:.4f} | "
                f"{document.metadata.get('source', 'Unknown PDF')} | "
                f"Page {document.metadata.get('page', 'Unknown')}"
            )


if __name__ == "__main__":
    question = input("Enter your question: ").strip()
    user_id = input(
        "Enter your authenticated Supabase user ID: "
    ).strip()

    debug_retrieval(
        query=question,
        user_id=user_id,
        k=4,
    )
