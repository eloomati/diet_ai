import uuid

from fastapi.testclient import TestClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> str:
    email = unique_email(prefix)
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass123"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_PROFILE_PAYLOAD = {
    "age": 29,
    "height_cm": 187,
    "weight_kg": 80,
    "activity_level": "HIGH",
    "goal": "MUSCLE_GAIN",
    "diet_type": "VEGETARIAN",
}


def test_create_profile_returns_201(client: TestClient) -> None:
    token = _register_and_login(client, "profile.create")

    response = client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    assert response.status_code == 201
    body = response.json()
    assert body["age"] == 29
    assert body["activity_level"] == "HIGH"
    assert body["goal"] == "MUSCLE_GAIN"
    assert body["diet_type"] == "VEGETARIAN"


def test_create_profile_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/profile", json=_PROFILE_PAYLOAD)

    assert response.status_code == 401


def test_create_profile_rejects_out_of_range_age(client: TestClient) -> None:
    token = _register_and_login(client, "profile.badage")

    response = client.post(
        "/api/v1/profile",
        json={**_PROFILE_PAYLOAD, "age": 200},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_create_profile_rejects_invalid_goal(client: TestClient) -> None:
    token = _register_and_login(client, "profile.badgoal")

    response = client.post(
        "/api/v1/profile",
        json={**_PROFILE_PAYLOAD, "goal": "NOT_A_REAL_GOAL"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_create_profile_twice_returns_409(client: TestClient) -> None:
    token = _register_and_login(client, "profile.duplicate")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    second = client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    assert second.status_code == 409
    assert second.json()["code"] == "CONFLICT"


def test_get_profile_without_one_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "profile.missing")

    response = client.get("/api/v1/profile", headers=_auth_headers(token))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_get_profile_returns_created_profile(client: TestClient) -> None:
    token = _register_and_login(client, "profile.get")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    response = client.get("/api/v1/profile", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json()["weight_kg"] == 80


def test_update_profile_changes_only_provided_fields(client: TestClient) -> None:
    token = _register_and_login(client, "profile.update")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))

    response = client.put(
        "/api/v1/profile",
        json={"weight_kg": 82, "activity_level": "VERY_HIGH"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["weight_kg"] == 82
    assert body["activity_level"] == "VERY_HIGH"
    assert body["age"] == 29
    assert body["diet_type"] == "VEGETARIAN"


def test_update_profile_without_one_returns_404(client: TestClient) -> None:
    token = _register_and_login(client, "profile.updatemissing")

    response = client.put("/api/v1/profile", json={"weight_kg": 82}, headers=_auth_headers(token))

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"


def test_each_user_has_their_own_profile(client: TestClient) -> None:
    token_a = _register_and_login(client, "profile.usera")
    token_b = _register_and_login(client, "profile.userb")

    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token_a))

    response_b = client.get("/api/v1/profile", headers=_auth_headers(token_b))

    assert response_b.status_code == 404
