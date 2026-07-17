from fastapi.testclient import TestClient

from backend.app.main import app


def test_generates_request_id_when_missing() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


def test_preserves_request_id_from_header() -> None:
    client = TestClient(app)
    request_id = "test-request-id-123"

    response = client.get("/api/v1/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id