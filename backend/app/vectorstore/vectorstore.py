
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document
from sqlalchemy import create_engine, text

project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

# Keep embedding requests small to avoid provider token limits.
EMBEDDING_BATCH_SIZE = 50

def connect_to_supabase() -> PGVector:

    database_url = os.getenv("SUPABASE_DATABASE_URL")
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL is missing.")

    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is missing.")

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        chunk_size=EMBEDDING_BATCH_SIZE,
    )

    vectorstore = PGVector(
        embeddings=embeddings,
        collection_name="STUDYMATE Documents",
        connection=database_url,
        use_jsonb=True,
    )

    return vectorstore

def add_documents(
    documents: list[Document],
    ids: list[str],
) -> list[str]:

    if not documents:
        return []

    if len(documents) != len(ids):
        raise ValueError("Each document must have exactly one ID.")

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs found in this upload.")

    vectorstore = connect_to_supabase()

    stored_ids = []

    for start in range(0, len(documents), EMBEDDING_BATCH_SIZE):

        end = start + EMBEDDING_BATCH_SIZE

        batch_documents = documents[start:end]
        batch_ids = ids[start:end]

        batch_stored_ids = vectorstore.add_documents(
            documents=batch_documents,
            ids=batch_ids,
        )

        stored_ids.extend(batch_stored_ids)

    return stored_ids

def replace_pdf_documents(
    documents: list[Document],
    ids: list[str],
    user_id: str,
    pdf_hash: str,
) -> list[str]:

    if not documents:
        raise ValueError("No readable PDF chunks were found.")

    if len(documents) != len(ids):
        raise ValueError("Each document must have exactly one ID.")

    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate chunk IDs found.")

    # Step 1: Validate ownership and PDF identity.
    for document in documents:

        if document.metadata.get("user_id") != user_id:
            raise ValueError("A chunk belongs to a different user.")

        if document.metadata.get("pdf_hash") != pdf_hash:
            raise ValueError("A chunk belongs to a different PDF.")

    # Step 2: Get the PDF filename.
    source = documents[0].metadata.get("source")

    if not source:
        raise ValueError("PDF filename is missing from metadata.")

    # Step 3: Connect to Supabase.
    vectorstore = connect_to_supabase()

    # Step 4: Save the new chunks in smaller batches.
    stored_ids = []

    for start in range(0, len(documents), EMBEDDING_BATCH_SIZE):

        end = start + EMBEDDING_BATCH_SIZE

        batch_documents = documents[start:end]
        batch_ids = ids[start:end]

        batch_stored_ids = vectorstore.add_documents(
            documents=batch_documents,
            ids=batch_ids,
        )

        stored_ids.extend(batch_stored_ids)

    # Step 5: Find older versions of this PDF.
    database_url = os.getenv("SUPABASE_DATABASE_URL")
    engine = create_engine(database_url)

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT e.id
                    FROM langchain_pg_embedding AS e
                    JOIN langchain_pg_collection AS c
                        ON e.collection_id = c.uuid
                    WHERE c.name = :collection_name
                      AND e.cmetadata ->> 'user_id' = :user_id
                      AND e.cmetadata ->> 'source' = :source
                      AND e.cmetadata ->> 'pdf_hash'
                          IS DISTINCT FROM :pdf_hash
                """),
                {
                    "collection_name": "STUDYMATE Documents",
                    "user_id": user_id,
                    "source": source,
                    "pdf_hash": pdf_hash,
                },
            )

            old_ids = [str(row.id) for row in result]

    finally:
        engine.dispose()

    # Step 6: Delete older versions after successful storage.
    if old_ids:
        vectorstore.delete(ids=old_ids)

    return stored_ids

def search_documents(
    query: str,
    k: int = 4,
    user_id: str | None = None,
) -> list[Document]:

    if not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not user_id:
        raise ValueError("user_id is required for document search.")

    vectorstore = connect_to_supabase()

    return vectorstore.similarity_search(
        query=query,
        k=k,
        filter={"user_id": user_id},
    )

def get_user_documents(user_id: str) -> list[Document]:

    if not user_id:
        raise ValueError("user_id is required.")

    database_url = os.getenv("SUPABASE_DATABASE_URL")

    if not database_url:
        raise ValueError("SUPABASE_DATABASE_URL is missing.")

    engine = create_engine(database_url)

    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT e.document, e.cmetadata
                    FROM langchain_pg_embedding AS e
                    JOIN langchain_pg_collection AS c
                        ON e.collection_id = c.uuid
                    WHERE c.name = :collection_name
                      AND e.cmetadata ->> 'user_id' = :user_id
                """),
                {
                    "collection_name": "STUDYMATE Documents",
                    "user_id": user_id,
                },
            )

            documents = []

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