from fastapi.testclient import TestClient

from backend.app.main import app


def test_health_endpoint_works():
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_frontend_origin():
    client = TestClient(app)
    response = client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_does_not_reflect_an_unconfigured_origin():
    client = TestClient(app)
    response = client.get("/api/v1/health", headers={"Origin": "http://evil.example.com"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers