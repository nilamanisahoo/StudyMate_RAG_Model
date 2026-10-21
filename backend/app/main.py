
from fastapi import FastAPI

app = FastAPI(
    title="StudyMate RAG API",
    description="Backend for the StudyMate PDF question-answering application",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "message": "Welcome to StudyMate RAG!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
