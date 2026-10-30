
from pydantic import BaseModel, Field, field_validator


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
        description="Question asked by the user about uploaded PDFs."
    )

    @field_validator("question", mode="before")
    @classmethod
    def validate_question(cls, value: str) -> str:
        if isinstance(value, str):
            value = value.strip()

        return value
