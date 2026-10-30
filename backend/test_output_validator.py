import pytest

from backend.app.security.output_validator import OutputValidator


def test_normal_output():
    text = "Python is a programming language."

    cleaned, warnings = OutputValidator.validate(text)

    assert cleaned == text
    assert warnings == []


def test_email_is_masked():
    text = "Contact student@gmail.com"

    cleaned, warnings = OutputValidator.validate(text)

    assert "student@gmail.com" not in cleaned
    assert "[EMAIL REDACTED]" in cleaned
    assert len(warnings) == 1


def test_multiple_pii_types():
    text = "Email: student@gmail.com"

    cleaned, warnings = OutputValidator.validate(text)

    assert "student@gmail.com" not in cleaned
    assert len(warnings) >= 1


def test_invalid_input():
    with pytest.raises(TypeError):
        OutputValidator.validate(123)