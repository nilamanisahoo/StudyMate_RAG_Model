import traceback
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    status,
    Request
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from .schemas.response import AnswerResponse
from .schemas.ask import QuestionRequest
from .authentication import verify_access_token
from .services.answer_service import answer_question
from .security.security_pipeline import SecurityPipeline
from .security.security_headers import SecurityHeadersMiddleware
limiter=Limiter(key_func=get_remote_address)
app = FastAPI(
    title="StudyMate RAG API",
    description="Backend for the StudyMate PDF question-answering application",
    version="0.1.0",
)
app.add_middleware(SecurityHeadersMiddleware)
app.state.limiter=limiter
app.add_exception_handler(
RateLimitExceeded,
_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

bearer_scheme = HTTPBearer(auto_error=False)
def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    """Verify the access token and return the authenticated user's ID."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_access_token(credentials.credentials)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except RuntimeError as error:
        # Server configuration problem, not a user's authentication failure.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is not configured correctly.",
        ) from error


@app.get("/")
def home():
    return {
        "message": "Welcome to StudyMate RAG!",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/ask",response_model=AnswerResponse)
@limiter.limit("10/minute")
def ask_question(
    request:Request,
    question_request: QuestionRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        cleaned_question,input_warnings=(
            SecurityPipeline.process_input(question_request.question)
        )
        print(cleaned_question)
        result= answer_question(
            question=cleaned_question,
            user_id=user_id,
        )
        cleaned_answer,output_warnings=(
            SecurityPipeline.process_output(result["answer"])
        )
        for warning in input_warnings+output_warnings:
            print("Security warning:", warning)

        return AnswerResponse(
            answer=cleaned_answer,
            sources=result.get("sources",[])
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    except Exception:
        print("Answer generation failed.")
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate an answer. Please try again later.",
    )