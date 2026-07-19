import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies.auth_dependencies import get_captcha_verifier
from backend.modules.identity.tests.fakes import FakeCaptchaVerifier


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


@pytest.fixture
def failing_captcha():
    app.dependency_overrides[get_captcha_verifier] = lambda: FakeCaptchaVerifier(should_pass=False)
    yield
    app.dependency_overrides.pop(get_captcha_verifier, None)


def test_register_returns_201(client: TestClient) -> None:
    email = unique_email("first.user")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["user_id"]


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    email = unique_email("dup.user")
    payload = {"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"}

    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_success_returns_200(client: TestClient) -> None:
    email = unique_email("login.user")

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_bad_credentials_returns_401(client: TestClient) -> None:
    email = unique_email("bad.creds")

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPass123"},
    )
    assert login.status_code == 401


def test_register_validation_returns_422_for_short_password(client: TestClient) -> None:
    email = unique_email("short.pass")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "123", "captcha_token": "test-captcha-token"},
    )
    assert response.status_code == 422


def test_login_validation_returns_422_for_missing_fields(client: TestClient) -> None:
    email = unique_email("missing.pass")
    response = client.post("/api/v1/auth/login", json={"email": email})
    assert response.status_code == 422


def test_register_missing_captcha_token_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": unique_email("no.captcha"), "password": "StrongPass123"},
    )
    assert response.status_code == 422


def test_register_with_failed_captcha_returns_400(client: TestClient, failing_captcha) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email("bad.captcha"),
            "password": "StrongPass123",
            "captcha_token": "bad-token",
        },
    )
    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"