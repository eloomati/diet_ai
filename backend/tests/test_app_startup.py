import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


def test_app_has_di_container():
    assert hasattr(app, "state")
    assert hasattr(app.state, "di_container")


def test_di_container_accessible_from_app():
    di_container = app.state.di_container
    ai_provider = di_container.get("ai_provider")

    assert ai_provider is not None


def test_health_endpoint_works():
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}