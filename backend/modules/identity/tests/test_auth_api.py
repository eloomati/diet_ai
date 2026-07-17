import os

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies.auth_dependencies import (
    get_login_user_use_case,
    get_register_user_use_case,
)
from backend.modules.identity.application import LoginUserUseCase, RegisterUserUseCase
from backend.modules.identity.tests.fakes import (
    FakePasswordHasher,
    FakeTokenService,
    InMemoryUserRepository,
)


def _build_test_client() -> TestClient:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()

    def _override_register_uc() -> RegisterUserUseCase:
        return RegisterUserUseCase(repo, hasher)

    def _override_login_uc() -> LoginUserUseCase:
        return LoginUserUseCase(repo, hasher, tokens)

    app.dependency_overrides[get_register_user_use_case] = _override_register_uc
    app.dependency_overrides[get_login_user_use_case] = _override_login_uc
    return TestClient(app)


def _cleanup_overrides() -> None:
    app.dependency_overrides.clear()


def test_register_then_login_flow() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": "api.user@example.com", "password": "StrongPass123"},
        )
        assert register_response.status_code in (200, 201)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "api.user@example.com", "password": "StrongPass123"},
        )
        assert login_response.status_code == 200
        body = login_response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
    finally:
        _cleanup_overrides()


def test_login_wrong_password_returns_401() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        client.post(
            "/api/v1/auth/register",
            json={"email": "wrong.pass@example.com", "password": "StrongPass123"},
        )

        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "wrong.pass@example.com", "password": "WrongPass123"},
        )
        assert login_response.status_code == 401
    finally:
        _cleanup_overrides()


def test_register_existing_email_returns_409() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        payload = {"email": "dup.api@example.com", "password": "StrongPass123"}

        r1 = client.post("/api/v1/auth/register", json=payload)
        assert r1.status_code in (200, 201)

        r2 = client.post("/api/v1/auth/register", json=payload)
        assert r2.status_code == 409
    finally:
        _cleanup_overrides()