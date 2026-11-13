
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
project_root = Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")

EMBEDDING_BATCH_SIZE = 50

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY is missing.")

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    chunk_size=EMBEDDING_BATCH_SIZE,
)

def generate_embeddings(
    text_chunks: list[str],
) -> list[list[float]]:

    if not text_chunks:
        return []

    return embeddings_model.embed_documents(text_chunks)

def generate_query_embedding(query: str) -> list[float]:

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    return embeddings_model.embed_query(query)