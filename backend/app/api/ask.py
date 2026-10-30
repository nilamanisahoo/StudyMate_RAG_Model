
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..schemas.ask import QuestionRequest
from ..schemas.response import AnswerResponse
from ..services.answer_service import answer_question
from ..security.security_pipeline import SecurityPipeline

from .dependencies import limiter, get_current_user_id


router = APIRouter()


@router.post("/ask", response_model=AnswerResponse)
@limiter.limit("10/minute")
def ask_question(
    request: Request,
    question_request: QuestionRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        cleaned_question, input_warnings = (
            SecurityPipeline.process_input(question_request.question)
        )

        result = answer_question(
            question=cleaned_question,
            user_id=user_id,
        )

        cleaned_answer, output_warnings = (
            SecurityPipeline.process_output(result["answer"])
        )

        for warning in input_warnings + output_warnings:
            print("Security warning:", warning)

        return AnswerResponse(
            answer=cleaned_answer,
            sources=result.get("sources", []),
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
