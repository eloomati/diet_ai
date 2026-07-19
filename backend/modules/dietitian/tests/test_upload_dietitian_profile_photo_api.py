import asyncio

from fastapi.testclient import TestClient

from backend.modules.dietitian.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian,
    promote_to_dietitian_with_profile,
    register_and_login,
)


def _upload(client: TestClient, token: str, filename: str = "photo.jpg", content_type: str = "image/jpeg"):
    return client.post(
        "/api/v1/dietitian/profile/photos",
        headers=auth_headers(token),
        files={"file": (filename, b"fake-bytes", content_type)},
    )


def test_upload_photo_returns_201_and_updates_profile(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.photo")
    asyncio.run(promote_to_dietitian_with_profile(user_id))

    response = _upload(client, token)

    assert response.status_code == 201
    body = response.json()
    assert len(body["photos"]) == 1
    assert body["photos"][0].startswith("/static/dietitian-photos/")


def test_upload_photo_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/dietitian/profile/photos",
        files={"file": ("photo.jpg", b"fake-bytes", "image/jpeg")},
    )

    assert response.status_code == 401


def test_upload_photo_requires_diet_user_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "dietitian.norole")

    response = _upload(client, token)

    assert response.status_code == 403


def test_upload_photo_returns_404_without_a_profile(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.noprofile")
    asyncio.run(promote_to_dietitian(user_id))

    response = _upload(client, token)

    assert response.status_code == 404


def test_upload_photo_rejects_unsupported_content_type(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.badtype")
    asyncio.run(promote_to_dietitian_with_profile(user_id))

    response = _upload(client, token, filename="doc.pdf", content_type="application/pdf")

    assert response.status_code == 400


def test_upload_photo_rejects_a_fourth_photo(client: TestClient) -> None:
    token, user_id = register_and_login(client, "dietitian.fourth")
    asyncio.run(promote_to_dietitian_with_profile(user_id))

    _upload(client, token)
    _upload(client, token)
    _upload(client, token)
    response = _upload(client, token)

    assert response.status_code == 400
