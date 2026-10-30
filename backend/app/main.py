
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from .api.ask import router as ask_router
from .api.dependencies import limiter
from .security.security_headers import SecurityHeadersMiddleware


# Create the FastAPI application.
app = FastAPI(
    title="StudyMate RAG API",
    description="Backend for the StudyMate PDF question-answering application",
    version="0.1.0",
)


# Configure CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# Add security headers middleware.
app.add_middleware(SecurityHeadersMiddleware)


# Configure the shared rate limiter.
app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

app.add_middleware(SlowAPIMiddleware)


# Register API routes.
app.include_router(ask_router)


# Home endpoint.
@app.get("/")
def home():
    return {
        "message": "Welcome to StudyMate RAG!",
        "status": "running",
    }


# Health-check endpoint.
@app.get("/health")
def health_check():
    return {"status": "healthy"}
