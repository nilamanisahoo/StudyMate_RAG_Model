
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.security.security_headers import (
    SecurityHeadersMiddleware,
)


def test_security_headers():
    test_app = FastAPI()

    test_app.add_middleware(SecurityHeadersMiddleware)

    @test_app.get("/")
    def home():
        return {"message": "StudyMate is running"}

    client = TestClient(test_app)

    response = client.get("/")

    assert response.status_code == 200

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"

    assert (
        response.headers["Referrer-Policy"]
        == "strict-origin-when-cross-origin"
    )

    assert (
        response.headers["Permissions-Policy"]
        == "camera=(), microphone=(), geolocation=()"
    )
