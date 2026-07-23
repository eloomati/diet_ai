import asyncio

from fastapi.testclient import TestClient

from backend.modules.dietitian.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian_with_profile,
    register_and_login,
)


def test_list_dietitians_is_public_and_includes_a_real_dietitian(client: TestClient) -> None:
    _, dietitian_id = register_and_login(client, "marketplace.list")
    asyncio.run(
        promote_to_dietitian_with_profile(dietitian_id, experience="7 years", description="Desc.")
    )

    response = client.get("/api/v1/dietitian")

    assert response.status_code == 200
    entries = [entry for entry in response.json() if entry["user_id"] == dietitian_id]
    assert len(entries) == 1
    assert entries[0]["experience"] == "7 years"
    assert entries[0]["average_rating"] is None
    assert entries[0]["review_count"] == 0


def test_get_public_profile_is_public_and_includes_reviews(client: TestClient) -> None:
    reviewer_token, _ = register_and_login(client, "marketplace.reviewer")
    _, dietitian_id = register_and_login(client, "marketplace.profile")
    asyncio.run(promote_to_dietitian_with_profile(dietitian_id, experience="12 years"))
    client.post(
        f"/api/v1/dietitian/{dietitian_id}/reviews",
        json={"rating": 7, "comment": "Solid guidance."},
        headers=auth_headers(reviewer_token),
    )

    response = client.get(f"/api/v1/dietitian/{dietitian_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["experience"] == "12 years"
    assert body["average_rating"] == 7.0
    assert body["review_count"] == 1
    assert len(body["reviews"]) == 1
    assert body["reviews"][0]["rating"] == 7
    assert body["reviews"][0]["comment"] == "Solid guidance."
    # No display_name set yet — resolves to the reviewer's email.
    assert "@" in body["reviews"][0]["reviewer_name"]
    assert "reviewer_id" not in body["reviews"][0]


def test_get_public_profile_returns_404_without_a_profile(client: TestClient) -> None:
    response = client.get("/api/v1/dietitian/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
