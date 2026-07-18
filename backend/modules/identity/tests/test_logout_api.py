import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    email = unique_email("logout.user")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    refresh_token = login.json()["refresh_token"]

    response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert response.status_code == 200

    refresh_attempt = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_attempt.status_code == 401


def test_logout_with_unknown_token_returns_200(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 200


def test_logout_twice_with_same_token_is_idempotent(client: TestClient) -> None:
    email = unique_email("logout.twice")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    refresh_token = login.json()["refresh_token"]

    first = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    second = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})

    assert first.status_code == 200
    assert second.status_code == 200


def test_other_sessions_survive_logout(client: TestClient) -> None:
    email = unique_email("logout.multisession")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )

    session_a = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    session_b = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    refresh_a = session_a.json()["refresh_token"]
    refresh_b = session_b.json()["refresh_token"]

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_a})
    assert logout.status_code == 200

    still_active = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_b})
    assert still_active.status_code == 200
