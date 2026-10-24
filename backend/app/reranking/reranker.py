from functools import lru_cache
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
@lru_cache(maxsize=1)
def get_reranker()->CrossEncoder:
    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_documents(query:str,documents:list[Document],top_k:int=4)->list[Document]:
    if not query.strip():
        raise ValueError("Query can't be empty.")
    if top_k<1:
        raise ValueError("top_k must be at least 1.")
    if not documents:
        return[]
    reranker=get_reranker()
    pairs=[
        (query,document.page_content)
        for document in documents
    ]
    scores=reranker.predict(pairs)
    scored_documents=list(zip(documents,scores))
    scored_documents.sort(key=lambda item: item[1],
                          reverse=True)
    return [
        document
        for document,score in scored_documents[:top_k]
    ]