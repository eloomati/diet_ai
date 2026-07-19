import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> str:
    email = unique_email(prefix)
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_APPLICATION_PAYLOAD = {
    "experience": "5 years as a clinical dietitian",
    "diplomas": ["MSc Dietetics", "Certified Sports Nutritionist"],
    "description": "I specialize in weight management and sports nutrition.",
}


def test_submit_application_returns_201(client: TestClient) -> None:
    token = _register_and_login(client, "dietitian.submit")

    response = client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["experience"] == _APPLICATION_PAYLOAD["experience"]
    assert body["diplomas"] == _APPLICATION_PAYLOAD["diplomas"]


def test_submit_application_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/dietitian/applications", json=_APPLICATION_PAYLOAD)

    assert response.status_code == 401


def test_submit_application_twice_returns_409(client: TestClient) -> None:
    token = _register_and_login(client, "dietitian.duplicate")
    client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=_auth_headers(token),
    )

    response = client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=_auth_headers(token),
    )

    assert response.status_code == 409


def test_get_my_application_returns_404_when_none_submitted(client: TestClient) -> None:
    token = _register_and_login(client, "dietitian.none")

    response = client.get("/api/v1/dietitian/applications/me", headers=_auth_headers(token))

    assert response.status_code == 404


def test_get_my_application_returns_submitted_application(client: TestClient) -> None:
    token = _register_and_login(client, "dietitian.get")
    client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=_auth_headers(token),
    )

    response = client.get("/api/v1/dietitian/applications/me", headers=_auth_headers(token))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["description"] == _APPLICATION_PAYLOAD["description"]


def test_submit_application_rejects_empty_experience(client: TestClient) -> None:
    token = _register_and_login(client, "dietitian.empty")

    response = client.post(
        "/api/v1/dietitian/applications",
        json={**_APPLICATION_PAYLOAD, "experience": ""},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
