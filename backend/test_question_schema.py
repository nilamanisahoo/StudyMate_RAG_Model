
import pytest
from pydantic import ValidationError

from backend.app.schemas.ask import QuestionRequest


def test_valid_question():
    request = QuestionRequest(
        question="What is industrial safety?"
    )

    assert request.question == "What is industrial safety?"


def test_empty_question_rejected():
    with pytest.raises(ValidationError):
        QuestionRequest(question="")


def test_whitespace_question_rejected():
    with pytest.raises(ValidationError):
        QuestionRequest(question="     ")


def test_question_with_extra_spaces_is_cleaned():
    request = QuestionRequest(
        question="  What is industrial safety?  "
    )

    assert request.question == "What is industrial safety?"


def test_question_over_2000_characters_rejected():
    with pytest.raises(ValidationError):
        QuestionRequest(question="a" * 2001)


def test_question_with_2000_characters_accepted():
    request = QuestionRequest(
        question="a" * 2000
    )

    assert len(request.question) == 2000
