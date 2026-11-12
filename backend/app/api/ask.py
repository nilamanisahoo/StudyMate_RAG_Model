
import traceback

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..schemas.ask import QuestionRequest
from ..schemas.response import AnswerResponse
from ..services.answer_service import answer_question
from ..security.security_pipeline import SecurityPipeline

from ..cache.response_cache import ResponseCache
from ..monitoring.logger import get_logger
from ..monitoring.metrics import MetricsCollector
from ..monitoring.timer import RequestTimer

from .dependencies import limiter, get_current_user_id


router = APIRouter()

# Shared instances for this backend process.
response_cache = ResponseCache(ttl_seconds=300)
metrics = MetricsCollector()
logger = get_logger("studymate-api")


@router.post("/ask", response_model=AnswerResponse)
@limiter.limit("10/minute")
def ask_question(
    request: Request,
    question_request: QuestionRequest,
    user_id: str = Depends(get_current_user_id),
):
    error_occurred = False
    cache_hit = False

    with RequestTimer() as timer:

        try:
            # Step 1: Validate and clean the user's question.
            cleaned_question, input_warnings = (
                SecurityPipeline.process_input(
                    question_request.question
                )
            )

            # Step 2: Check whether an answer is already cached.
            cached_result = response_cache.get(
                query=cleaned_question,
                user_id=user_id,
            )

            if cached_result is not None:
                cache_hit = True

                logger.info(
                    "Returning cached answer",
                    extra={
                        "extra_data": {
                            "user_id": user_id,
                            "cache_hit": True,
                        }
                    },
                )

                return AnswerResponse(**cached_result)

            # Step 3: Generate an answer using the existing RAG pipeline.
            result = answer_question(
                question=cleaned_question,
                user_id=user_id,
            )

            # Step 4: Apply output security checks.
            cleaned_answer, output_warnings = (
                SecurityPipeline.process_output(
                    result["answer"]
                )
            )

            # Step 5: Log security warnings.
            for warning in input_warnings + output_warnings:
                logger.warning(
                    "Security warning",
                    extra={
                        "extra_data": {
                            "user_id": user_id,
                            "warning": str(warning),
                        }
                    },
                )

            # Step 6: Prepare the final API response.
            final_result = AnswerResponse(
                answer=cleaned_answer,
                sources=result.get("sources", []),
            )

            # Step 7: Store the response in the cache.
            response_cache.set(
                query=cleaned_question,
                user_id=user_id,
                response=final_result.model_dump(),
            )

            return final_result

        except ValueError as error:
            error_occurred = True

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

        except Exception as error:
            error_occurred = True

            logger.error(
                "Answer generation failed",
                extra={
                    "extra_data": {
                        "user_id": user_id,
                        "error": str(error),
                    }
                },
            )

            traceback.print_exc()

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Failed to generate an answer. "
                    "Please try again later."
                ),
            ) from error

        finally:
            # Step 8: Record request performance metrics.
            metrics.record_request(
                latency_ms=timer.elapsed_ms,
                error=error_occurred,
                cache_hit=cache_hit,
            )

            logger.info(
                "Ask request completed",
                extra={
                    "extra_data": {
                        "user_id": user_id,
                        "latency_ms": round(
                            timer.elapsed_ms, 2
                        ),
                        "cache_hit": cache_hit,
                        "error": error_occurred,
                    }
                },
            )
