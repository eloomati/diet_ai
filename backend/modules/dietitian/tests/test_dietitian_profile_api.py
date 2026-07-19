import asyncio

from fastapi.testclient import TestClient

from backend.modules.dietitian.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian,
    promote_to_dietitian_with_profile,
    register_and_login,
)


def test_get_my_profile_returns_200(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.get")
    asyncio.run(promote_to_dietitian_with_profile(user_id, experience="10 years"))

    response = client.get("/api/v1/dietitian/profile/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["experience"] == "10 years"


def test_get_my_profile_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/dietitian/profile/me")

    assert response.status_code == 401


def test_get_my_profile_requires_diet_user_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "dietitian.profile.norole")

    response = client.get("/api/v1/dietitian/profile/me", headers=auth_headers(token))

    assert response.status_code == 403


def test_get_my_profile_returns_404_without_a_profile(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.noprofile")
    asyncio.run(promote_to_dietitian(user_id))

    response = client.get("/api/v1/dietitian/profile/me", headers=auth_headers(token))

    assert response.status_code == 404


def test_update_profile_changes_only_given_fields(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.update")
    asyncio.run(promote_to_dietitian_with_profile(user_id, experience="5 years"))

    response = client.put(
        "/api/v1/dietitian/profile",
        headers=auth_headers(token),
        json={"description": "Updated description."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] == "Updated description."
    assert body["experience"] == "5 years"


def test_update_profile_rejects_blanking_out_experience(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.badupdate")
    asyncio.run(promote_to_dietitian_with_profile(user_id))

    response = client.put(
        "/api/v1/dietitian/profile",
        headers=auth_headers(token),
        json={"experience": "   "},
    )

    assert response.status_code == 400


def test_remove_photo_drops_it_from_the_profile(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.removephoto")
    asyncio.run(promote_to_dietitian_with_profile(user_id))
    upload = client.post(
        "/api/v1/dietitian/profile/photos",
        headers=auth_headers(token),
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
    )
    assert upload.status_code == 201

    response = client.delete("/api/v1/dietitian/profile/photos/0", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["photos"] == []


def test_remove_photo_rejects_an_out_of_range_index(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.profile.removebad")
    asyncio.run(promote_to_dietitian_with_profile(user_id))

    response = client.delete("/api/v1/dietitian/profile/photos/0", headers=auth_headers(token))

    assert response.status_code == 400
