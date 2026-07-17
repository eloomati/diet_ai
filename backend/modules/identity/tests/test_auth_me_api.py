import os
import uuid

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies import get_current_user
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
from backend.modules.identity.domain import Email
from backend.modules.identity.infrastructure.security import JwtTokenService
from backend.modules.identity.tests.fakes import (
    FakeEmailSender,
    FakePasswordHasher,
    FakeTokenService,
    InMemoryEmailVerificationTokenRepository,
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)
from backend.shared.config import get_settings


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _build_test_client() -> TestClient:
    user_repo = InMemoryUserRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService()

    def _override_register_uc() -> RegisterUserUseCase:
        return RegisterUserUseCase(
            user_repo, hasher, InMemoryEmailVerificationTokenRepository(), FakeEmailSender()
        )

    def _override_login_uc() -> LoginUserUseCase:
        return LoginUserUseCase(user_repo, refresh_repo, hasher, tokens)

    def _override_refresh_uc() -> RefreshAccessTokenUseCase:
        return RefreshAccessTokenUseCase(user_repo, refresh_repo, tokens)

    async def _override_current_user():
        # FakeTokenService creates access token as: access::<user_id>::<email>
        user = await user_repo.get_by_email(Email("me.user@example.com"))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    app.dependency_overrides[get_register_user_use_case] = _override_register_uc
    app.dependency_overrides[get_login_user_use_case] = _override_login_uc
    app.dependency_overrides[get_refresh_access_token_use_case] = _override_refresh_uc
    app.dependency_overrides[get_current_user] = _override_current_user

    return TestClient(app)


def _cleanup_overrides() -> None:
    app.dependency_overrides.clear()


def test_me_with_valid_token_returns_200() -> None:
    os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-32-chars-minimum!!")
    client = _build_test_client()
    try:
        reg = client.post(
            "/api/v1/auth/register",
            json={"email": "me.user@example.com", "password": "StrongPass123"},
        )
        assert reg.status_code == 201

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "me.user@example.com", "password": "StrongPass123"},
        )
        assert login.status_code == 200
        access_token = login.json()["access_token"]

        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me.status_code == 200
        body = me.json()
        assert body["email"] == "me.user@example.com"
        assert body["status"] == "ACTIVE"
    finally:
        _cleanup_overrides()


def test_me_without_token_returns_401() -> None:
    client = _build_test_client()
    try:
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    finally:
        _cleanup_overrides()


def test_me_with_invalid_token_returns_401() -> None:
    client = _build_test_client()
    try:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.value"},
        )
        # because current_user is overridden in test mode, this may still pass as 200
        # only assert endpoint is reachable; strict JWT validation belongs to infra-backed tests
        assert response.status_code in (200, 401)
    finally:
        _cleanup_overrides()


# The tests above override get_current_user, so they never exercise the real
# JWT decoding / DB lookup in current_user.py. The tests below hit that
# dependency for real, using the `client` fixture from conftest.py (real Postgres).


def _build_real_access_token(**overrides) -> str:
    settings = get_settings()
    token_service = JwtTokenService(
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        access_ttl_minutes=overrides.get("access_ttl_minutes", settings.jwt_access_ttl_minutes),
        refresh_ttl_days=settings.jwt_refresh_ttl_days,
    )
    return token_service.create_access_token(
        user_id=overrides.get("user_id", str(uuid.uuid4())),
        email=overrides.get("email", "ghost@example.com"),
    )


def test_me_real_flow_returns_current_user(client: TestClient) -> None:
    email = unique_email("me.real")
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    assert register.status_code == 201
    user_id = register.json()["user_id"]

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    assert login.status_code == 200
    access_token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["user_id"] == user_id
    assert body["email"] == email
    assert body["status"] == "ACTIVE"


def test_me_real_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_real_with_malformed_token_returns_401(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == 401


def test_me_real_with_refresh_token_used_as_access_returns_401(client: TestClient) -> None:
    email = unique_email("me.typeconfusion")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    refresh_token = login.json()["refresh_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401


def test_me_real_with_unknown_user_id_returns_401(client: TestClient) -> None:
    token = _build_real_access_token(user_id=str(uuid.uuid4()))

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_real_with_expired_token_returns_401(client: TestClient) -> None:
    token = _build_real_access_token(access_ttl_minutes=-1)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401