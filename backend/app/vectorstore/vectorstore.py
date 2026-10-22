import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

project_root=Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

def connect_to_supabase()->PGVector:
    database_url=os.getenv("SUPABASE_DATABASE_URL")
    api_key=os.getenv("OPENROUTER_API_KEY")
    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL is missing from .env")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing from .env")
    embeddings=OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )
    vectorstore=PGVector(
        embeddings=embeddings,
        collection_name="STUDYMATE Documents",
        connection=database_url,
        use_jsonb=True
    )
    return vectorstore

def add_documents(documents:list[Document])->list[str]:
    if not documents:
        return []
    vectorstore=connect_to_supabase()
    return vectorstore.add_documents(documents)

def search_documents(query:str,k:int=4)->list[Document]:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    vectorstore=connect_to_supabase()
    return vectorstore.similarity_search(query=query,k=k)
