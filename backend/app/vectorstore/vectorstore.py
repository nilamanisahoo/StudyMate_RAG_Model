import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from sqlalchemy import create_engine,text

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

def add_documents(documents:list[Document],ids:list[str])->list[str]:
    if not documents:
        return []
    if len(documents) != len(ids):
        raise ValueError("Each document must have exactly one ID.")

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs found in this upload.")
    vectorstore=connect_to_supabase()
    return vectorstore.add_documents(documents=documents,ids=ids)

def search_documents(query:str,k:int=4,user_id:str|None=None)->list[Document]:
    if not query.strip():
        raise ValueError("Search query cannot be empty.")
    if not user_id:
        raise ValueError("user_id is required for document search.")
    vectorstore=connect_to_supabase()
    return vectorstore.similarity_search(query=query,k=k,filter={"user_id":user_id})

def get_user_documents(user_id:str)->list[Document]:
    if not user_id :
        raise ValueError("user_id is required.")
    database_url=os.getenv("SUPABASE_DATABASE_URL")
    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL is missing from .env")
    engine=create_engine(database_url)
    try:
        with engine.connect() as connection:
            result=connection.execute(
                text("""
                    SELECT e.document,e.cmetadata
                    FROM langchain_pg_embedding AS e
                    JOIN langchain_pg_collection as c
                        ON e.collection_id = c.uuid
                    WHERE c.name =:collection_name
                      AND e.cmetadata ->> 'user_id'=:user_id
                """),
                {
                    "collection_name":"STUDYMATE Documents",
                    "user_id":user_id,
                },
            )
            documents=[]
            for row in result:
                documents.append(
                    Document(
                        page_content=row.document,
                        metadata=row.cmetadata or {},
                    )
                )
            return documents
    finally:
        engine.dispose()