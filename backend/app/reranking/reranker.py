
import os
from functools import lru_cache

from langchain_core.documents import Document


@lru_cache(maxsize=1)
def get_reranker():
    """
    Load CrossEncoder only when reranking is enabled.
    """
    if os.getenv("ENABLE_RERANKING", "false").lower() != "true":
        return None

    from sentence_transformers import CrossEncoder

    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def rerank_documents(
    query: str,
    documents: list[Document],
    top_k: int = 4,
) -> list[Document]:

    if not query.strip():
        raise ValueError("Query can't be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    if not documents:
        return []

    reranker = get_reranker()

    # If reranking is disabled, return the original retrieval results.
    if reranker is None:
        return documents[:top_k]

    pairs = [
        (query, document.page_content)
        for document in documents
    ]

    scores = reranker.predict(pairs)

    scored_documents = list(zip(documents, scores))

    scored_documents.sort(
        key=lambda item: float(item[1]),
        reverse=True,
    )

    return [
        document
        for document, score in scored_documents[:top_k]
    ]
