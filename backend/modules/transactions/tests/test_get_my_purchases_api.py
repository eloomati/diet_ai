import asyncio

from fastapi.testclient import TestClient

from backend.modules.transactions.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian,
    register_and_login,
    verify_email,
)


def test_get_my_purchases_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/transactions/me/purchases")

    assert response.status_code == 401


def test_get_my_purchases_works_for_any_authenticated_user(client: TestClient) -> None:
    buyer_token, _ = register_and_login(client, "txn.purchaser")

    response = client.get("/api/v1/transactions/me/purchases", headers=auth_headers(buyer_token))

    assert response.status_code == 200
    assert response.json() == []


def test_get_my_purchases_returns_only_the_buyers_own_transactions(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "txn.mypurchases")
    _, dietitian_id = register_and_login(client, "txn.mypurchasesdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    other_buyer_token, other_buyer_id = register_and_login(client, "txn.otherpurchaser")
    asyncio.run(verify_email(buyer_id))
    asyncio.run(verify_email(other_buyer_id))

    client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )
    client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "INDIVIDUAL_PLAN"},
        headers=auth_headers(other_buyer_token),
    )

    response = client.get("/api/v1/transactions/me/purchases", headers=auth_headers(buyer_token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["dietitian_id"] == dietitian_id
    assert body[0]["offer_type"] == "PLAN_REVIEW"
