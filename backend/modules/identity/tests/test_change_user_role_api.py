import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import Email, PasswordHash, Role, User


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _override_current_user_as(role: Role):
    async def _override() -> User:
        user = User.create(
            email=Email(f"caller.{uuid.uuid4().hex[:10]}@example.com"),
            password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
        )
        user.change_role(role)
        return user

    return _override


def _cleanup_overrides() -> None:
    app.dependency_overrides.clear()


def test_super_admin_can_change_a_users_role(client: TestClient) -> None:
    email = unique_email("role.target")
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    assert register.status_code == 201
    user_id = register.json()["user_id"]

    app.dependency_overrides[get_current_user] = _override_current_user_as(Role.SUPER_ADMIN)
    try:
        response = client.patch(
            f"/api/v1/admin/users/{user_id}/role",
            json={"new_role": "DIET_USER"},
        )
    finally:
        _cleanup_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == user_id
    assert body["email"] == email
    assert body["role"] == "DIET_USER"

    # Persistence, not just the response body — this is exactly the code
    # path Etap 0 Stage 1 found broken (the repository's update branch was
    # missing `role`), so this closes the loop for real over HTTP.
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPass123"},
    )
    access_token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me.json()["role"] == "DIET_USER"


def test_non_super_admin_cannot_change_a_users_role(client: TestClient) -> None:
    email = unique_email("role.forbidden")
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    user_id = register.json()["user_id"]

    for role in (Role.USER, Role.DIET_USER, Role.ADMIN):
        app.dependency_overrides[get_current_user] = _override_current_user_as(role)
        try:
            response = client.patch(
                f"/api/v1/admin/users/{user_id}/role",
                json={"new_role": "ADMIN"},
            )
        finally:
            _cleanup_overrides()

        assert response.status_code == 403, f"role {role} should not be allowed to change roles"
        assert response.json()["code"] == "FORBIDDEN"


def test_change_role_for_unknown_user_returns_404(client: TestClient) -> None:
    app.dependency_overrides[get_current_user] = _override_current_user_as(Role.SUPER_ADMIN)
    try:
        response = client.patch(
            f"/api/v1/admin/users/{uuid.uuid4()}/role",
            json={"new_role": "ADMIN"},
        )
    finally:
        _cleanup_overrides()

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_change_role_rejects_unknown_role_value(client: TestClient) -> None:
    email = unique_email("role.invalid")
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    user_id = register.json()["user_id"]

    app.dependency_overrides[get_current_user] = _override_current_user_as(Role.SUPER_ADMIN)
    try:
        response = client.patch(
            f"/api/v1/admin/users/{user_id}/role",
            json={"new_role": "NOT_A_REAL_ROLE"},
        )
    finally:
        _cleanup_overrides()

    assert response.status_code == 422


def test_super_admin_cannot_change_their_own_role(client: TestClient) -> None:
    email = unique_email("role.self")
    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    user_id = register.json()["user_id"]

    async def _override_as_self() -> User:
        user = User.create(email=Email(email), password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"))
        user.id = uuid.UUID(user_id)
        user.change_role(Role.SUPER_ADMIN)
        return user

    app.dependency_overrides[get_current_user] = _override_as_self
    try:
        response = client.patch(
            f"/api/v1/admin/users/{user_id}/role",
            json={"new_role": "ADMIN"},
        )
    finally:
        _cleanup_overrides()

    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"


def test_change_user_role_without_auth_returns_401(client: TestClient) -> None:
    response = client.patch(
        f"/api/v1/admin/users/{uuid.uuid4()}/role",
        json={"new_role": "ADMIN"},
    )
    assert response.status_code == 401
