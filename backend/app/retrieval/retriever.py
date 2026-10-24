from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document
from ..vectorstore.vectorstore import(
    connect_to_supabase,
    get_user_documents
)

def create_hybrid_retriever(
        user_id:str,
        k:int=4
)->EnsembleRetriever:
    if not user_id:
        raise ValueError("user_id is required.")
    if k<1:
        raise ValueError("K must be at least 1.")
    documents=get_user_documents(user_id)
    if not documents:
        raise ValueError("No PDF found for this user in supabase.")
    vectorstore=connect_to_supabase()
    semantic_retriever=vectorstore.as_retriever(
        search_kwargs={
            "k":k,
            "filter":{"user_id":user_id}
        }
    )
    Keyword_retriever=BM25Retriever.from_documents(
        documents=documents,
        k=k
    )
    hybrid_retriever=EnsembleRetriever(
        retrievers=[
            semantic_retriever,
            Keyword_retriever
        ],
        weights=[0.5,0.5]
    )
    return hybrid_retriever
def hybrid_search(
        query:str,
        user_id:str,
        k:int=4
)->list[Document]:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    retriever=create_hybrid_retriever(user_id=user_id,k=k)
    results=retriever.invoke(query)
    return results

