from fastapi import APIRouter
from fastapi.testclient import TestClient

from backend.app.main import app


def test_error_format_contains_code_message_timestamp() -> None:
    router = APIRouter()

    @router.get("/_raise")
    async def raise_error() -> None:
        raise RuntimeError("boom")

    app.include_router(router, prefix="/api/v1")
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/api/v1/_raise")
    body = response.json()

    assert response.status_code == 500
    assert body["code"] == "INTERNAL_ERROR"
    assert "message" in body
    assert "timestamp" in body
    assert body["timestamp"].endswith("Z")