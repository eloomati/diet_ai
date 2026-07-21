import asyncio

from fastapi.testclient import TestClient

from backend.modules.dietitian.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian,
    promote_to_dietitian_with_profile,
    register_and_login,
)


def test_submit_review_returns_201(client: TestClient) -> None:
    reviewer_token, _ = register_and_login(client, "review.reviewer")
    _, dietitian_id = register_and_login(client, "review.dietitian")
    asyncio.run(promote_to_dietitian(dietitian_id))

    response = client.post(
        f"/api/v1/dietitian/{dietitian_id}/reviews",
        json={"rating": 9, "comment": "Very helpful, clear plan."},
        headers=auth_headers(reviewer_token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["rating"] == 9
    assert body["dietitian_id"] == dietitian_id


def test_submit_review_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/dietitian/00000000-0000-0000-0000-000000000000/reviews",
        json={"rating": 5, "comment": "N/A"},
    )

    assert response.status_code == 401


def test_submit_review_returns_404_for_unknown_dietitian(client: TestClient) -> None:
    reviewer_token, _ = register_and_login(client, "review.nodiet")

    response = client.post(
        "/api/v1/dietitian/00000000-0000-0000-0000-000000000000/reviews",
        json={"rating": 5, "comment": "N/A"},
        headers=auth_headers(reviewer_token),
    )

    assert response.status_code == 404


def test_submit_review_rejects_reviewing_yourself(client: TestClient) -> None:
    token, user_id = register_and_login(client, "review.self")
    asyncio.run(promote_to_dietitian(user_id))

    response = client.post(
        f"/api/v1/dietitian/{user_id}/reviews",
        json={"rating": 8, "comment": "Self-praise."},
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_submit_review_rejects_out_of_range_rating(client: TestClient) -> None:
    reviewer_token, _ = register_and_login(client, "review.badrating")
    _, dietitian_id = register_and_login(client, "review.badratingdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))

    response = client.post(
        f"/api/v1/dietitian/{dietitian_id}/reviews",
        json={"rating": 11, "comment": "Too high."},
        headers=auth_headers(reviewer_token),
    )

    assert response.status_code == 422


def test_submit_review_upserts_on_a_second_submission(client: TestClient) -> None:
    reviewer_token, _ = register_and_login(client, "review.upsert")
    _, dietitian_id = register_and_login(client, "review.upsertdiet")
    asyncio.run(promote_to_dietitian_with_profile(dietitian_id))
    client.post(
        f"/api/v1/dietitian/{dietitian_id}/reviews",
        json={"rating": 4, "comment": "First impression."},
        headers=auth_headers(reviewer_token),
    )

    response = client.post(
        f"/api/v1/dietitian/{dietitian_id}/reviews",
        json={"rating": 9, "comment": "Updated after more sessions."},
        headers=auth_headers(reviewer_token),
    )

    assert response.status_code == 201
    assert response.json()["rating"] == 9

    public_profile = client.get(f"/api/v1/dietitian/{dietitian_id}")
    assert public_profile.json()["review_count"] == 1
