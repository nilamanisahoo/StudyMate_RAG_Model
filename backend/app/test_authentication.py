
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api import dependencies as api_dependencies
from backend.app.api import ask as ask_api


client = TestClient(app)


def test_ask_without_token_returns_401():
    response = client.post(
        "/ask",
        json={"question": "What is industrial safety?"},
    )

    assert response.status_code == 401


def test_ask_with_invalid_token_returns_401(monkeypatch):
    def reject_token(token):
        raise ValueError("Invalid token")

    monkeypatch.setattr(
        api_dependencies,
        "verify_access_token",
        reject_token,
    )

    response = client.post(
        "/ask",
        headers={"Authorization": "Bearer fake-token"},
        json={"question": "What is industrial safety?"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or expired access token. Please log in again."
    )


def test_ask_uses_verified_user_id(monkeypatch):
    def accept_test_token(token):
        assert token == "test-token"
        return "verified-user-123"

    def fake_answer_question(question, user_id):
        return {
            "answer": "Test answer",
            "user_id_used": user_id,
        }

    monkeypatch.setattr(
        api_dependencies,
        "verify_access_token",
        accept_test_token,
    )

    monkeypatch.setattr(
        ask_api,
        "answer_question",
        fake_answer_question,
    )

    response = client.post(
        "/ask",
        headers={"Authorization": "Bearer test-token"},
        json={
            "question": "What is industrial safety?",
            "user_id": "someone-elses-id",
        },
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Test answer"
