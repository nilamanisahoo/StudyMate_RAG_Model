
from ..retrieval.retriever import create_hybrid_retriever
from ..reranking.reranker import (
    get_reranker,
    rerank_documents,
)


def debug_retrieval(
    query: str,
    user_id: str,
    k: int = 4,
    min_score: float = 0.0,
) -> None:
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if not user_id:
        raise ValueError("user_id is required.")

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

    filtered_documents = rerank_documents(
        query=query,
        documents=candidates,
        top_k=k,
        min_score=min_score,
    )

    print(f"\nQuestion: {query}")
    print(f"Candidate chunks: {len(candidates)}")
    print(f"Minimum score: {min_score}")
    print(f"Qualifying chunks kept: {len(filtered_documents)}")

    print("\n--- Original ranking ---")

    for rank, (document, score) in enumerate(
        ranked[:k],
        start=1,
    ):
        source = document.metadata.get("source", "Unknown PDF")
        page = document.metadata.get("page", "Unknown")
        decision = "KEEP" if float(score) >= min_score else "REMOVE"

        print(
            f"\nRank {rank} | Score: {float(score):.4f}"
            f" | {decision}"
        )
        print(f"Source: {source} | Page: {page}")
        print(document.page_content[:300])

    print("\n--- Final filtered results ---")

    for rank, document in enumerate(
        filtered_documents,
        start=1,
    ):
        print(
            f"{rank}. {document.metadata.get('source', 'Unknown PDF')}"
            f" | Page {document.metadata.get('page', 'Unknown')}"
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
        min_score=0.0,
    )
