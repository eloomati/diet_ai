import os

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies.auth_dependencies import (
    get_login_user_use_case,
    get_refresh_access_token_use_case,
    get_register_user_use_case,
)
from backend.modules.identity.application import (
    LoginUserUseCase,
    RefreshAccessTokenUseCase,
    RegisterUserUseCase,
)
from backend.modules.identity.tests.fakes import (
    FakePasswordHasher,
    FakeTokenService,
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)


def _build_test_client() -> TestClient:
    user_repo = InMemoryUserRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()

    def _override_register_uc() -> RegisterUserUseCase:
        return RegisterUserUseCase(user_repo, hasher)

    def _override_login_uc() -> LoginUserUseCase:
        return LoginUserUseCase(user_repo, refresh_repo, hasher, tokens)

    def _override_refresh_uc() -> RefreshAccessTokenUseCase:
        return RefreshAccessTokenUseCase(user_repo, refresh_repo, tokens)

    app.dependency_overrides[get_register_user_use_case] = _override_register_uc
    app.dependency_overrides[get_login_user_use_case] = _override_login_uc
    app.dependency_overrides[get_refresh_access_token_use_case] = _override_refresh_uc

    return TestClient(app)


def _cleanup_overrides() -> None:
    app.dependency_overrides.clear()


def test_refresh_flow_returns_new_tokens() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": "refresh.user@example.com", "password": "StrongPass123"},
        )
        assert reg.status_code == 201

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh.user@example.com", "password": "StrongPass123"},
        )
        assert login.status_code == 200
        old_refresh = login.json()["refresh_token"]

        refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert refresh.status_code == 200
        body = refresh.json()

        assert "access_token" in body
        assert "refresh_token" in body
        assert body["refresh_token"] != old_refresh
        assert body["token_type"] == "bearer"
    finally:
        _cleanup_overrides()


def test_refresh_with_invalid_token_returns_401() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid"})
        assert response.status_code == 401
    finally:
        _cleanup_overrides()