
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.middleware.cors import CORSMiddleware


def create_test_app():
    test_app = FastAPI()

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:8501",
            "http://127.0.0.1:8501",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @test_app.get("/")
    def home():
        return {"message": "StudyMate is running"}

    return test_app


def test_allowed_origin():
    client = TestClient(create_test_app())

    response = client.get(
        "/",
        headers={"Origin": "http://localhost:8501"},
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:8501"
    )


def test_disallowed_origin():
    client = TestClient(create_test_app())

    response = client.get(
        "/",
        headers={"Origin": "https://untrusted-example.com"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_preflight_request():
    client = TestClient(create_test_app())

    response = client.options(
        "/ask",
        headers={
            "Origin": "http://localhost:8501",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "http://localhost:8501"
    )
