
from backend.app.security.pii_detector import PIIDetector


def test_detect_email():
    text = "Contact me at student@gmail.com"

    result = PIIDetector.detect(text)

    assert "email" in result
    assert "student@gmail.com" in result["email"]


def test_detect_multiple_emails():
    text = "Emails: a@gmail.com and b@yahoo.com"

    result = PIIDetector.detect(text)

    assert len(result["email"]) == 2


def test_mask_email():
    text = "Contact me at student@gmail.com"

    result = PIIDetector.mask(text)

    assert result == "Contact me at [EMAIL REDACTED]"


def test_no_pii():
    text = "What is Python?"

    result = PIIDetector.detect(text)

    assert result == {}


def test_mask_multiple_pii():
    text = "Email: student@gmail.com"

    result = PIIDetector.mask(text)

    assert "[EMAIL REDACTED]" in result
    assert "student@gmail.com" not in result
