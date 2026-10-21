from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv
from pathlib import Path
import os
project_root=Path(__file__).resolve().parents[3]
load_dotenv(project_root / ".env")
embeddings_model=OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)
def generate_embeddings(text_chunks:list[str])->list[list[float]]:
    if not text_chunks:
        return []
    return embeddings_model.embed_documents(text_chunks)
def generate_query_embedding(query:str)->list[float]:
    if not query.strip():
        raise ValueError("Query cannot be empty.")
    return embeddings_model.embed_query(query)
