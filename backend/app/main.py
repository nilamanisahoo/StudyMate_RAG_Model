
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from .services.answer_service import answer_question

app = FastAPI(
    title="StudyMate RAG API",
    description="Backend for the StudyMate PDF question-answering application",
    version="0.1.0",
)

class QuestionRequest(BaseModel):
    question:str=Field(min_length=1)
    user_id:str=Field(min_length=1)

@app.get("/")
def home():
    return {
        "message": "Welcome to StudyMate RAG!",
        "status": "running",
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/ask")
def ask_question(request:QuestionRequest):
    try:
        return answer_question(
            question=request.question,
            user_id=request.user_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate an answer. Check the backend terminal.",
        ) from error
