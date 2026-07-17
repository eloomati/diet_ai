import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def test_register_returns_201(client: TestClient) -> None:
    email = unique_email("first.user")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["user_id"]


def test_register_duplicate_email_returns_409(client: TestClient) -> None:
    email = unique_email("dup.user")
    payload = {"email": email, "password": "StrongPass123"}

    first = client.post("/api/v1/auth/register", json=payload)
    second = client.post("/api/v1/auth/register", json=payload)

    assert first.status_code == 201
    assert second.status_code == 409


def test_login_success_returns_200(client: TestClient) -> None:
    email = unique_email("login.user")

    register = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123"},
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
        json={"email": email, "password": "StrongPass123"},
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
        json={"email": email, "password": "123"},
    )
    assert response.status_code == 422


def test_login_validation_returns_422_for_missing_fields(client: TestClient) -> None:
    email = unique_email("missing.pass")
    response = client.post("/api/v1/auth/login", json={"email": email})
    assert response.status_code == 422