import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from ..retrieval.retriever import hybrid_search

project_root=Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

def create_chat_model()->ChatOpenAI:
    api_key=os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from .env")
    return ChatOpenAI(
        model="gpt-4o-mini",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0
    )

def answer_question(
        question:str,
        user_id:str,
        k:int=4,
)->dict:
    if not question.strip():
        raise ValueError("Question cannot be empty.")
    documents:list[Document]=hybrid_search(
        query=question,
        user_id=user_id,
        k=k
    )
    if not documents:
        return {
            "answer": "I couldn't find relevant information in your PDFs.",
            "sources":[]
        }
    context_parts=[]
    sources=[]
    seen_sources=set()
    for document in documents:
        source=document.metadata.get("source","Unknown PDF")
        page=document.metadata.get("page","Unknown")
        context_parts.append(
            f"Source: {source}, page: {page}\n"
            f"Content: {document.page_content}"
        )
        source_key=(source,page)
        if source_key not in seen_sources:
            sources.append({"source": source, "page": page})
            seen_sources.add(source_key)
    context= "\n\n".join(context_parts)
    model=create_chat_model()
    response=model.invoke(
        [
            (
                "system",
                "You are StudyMate, a helpful PDF question-answering assistant. "
                "Answer using only the supplied PDF context. "
                "If the context does not contain the answer, say you could not "
                "find the answer in the uploaded PDFs. "
                "Do not invent facts or sources. Be clear and beginner-friendly.",
            ),
            (
                "human",
                f"Question:\n{question}\n\n"
                f"PDF content:\n{context}",
            )
        ]
    )
    return {
        "answer":response.content,
        "sources":sources
    }