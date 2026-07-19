import asyncio

from fastapi.testclient import TestClient

from backend.modules.transactions.tests.db_helpers import (
    auth_headers,
    promote_to_dietitian,
    register_and_login,
)


def test_create_transaction_returns_201(client: TestClient) -> None:
    buyer_token, _ = register_and_login(client, "txn.buyer")
    _, dietitian_id = register_and_login(client, "txn.dietitian")
    asyncio.run(promote_to_dietitian(dietitian_id))

    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "UNPAID"
    assert body["offer_type"] == "PLAN_REVIEW"
    assert body["amount"] == "49.00"
    assert body["dietitian_id"] == dietitian_id


def test_create_transaction_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": "00000000-0000-0000-0000-000000000000", "offer_type": "PLAN_REVIEW"},
    )

    assert response.status_code == 401


def test_create_transaction_returns_404_for_unknown_dietitian(client: TestClient) -> None:
    buyer_token, _ = register_and_login(client, "txn.buyernodiet")

    response = client.post(
        "/api/v1/transactions",
        json={
            "dietitian_id": "00000000-0000-0000-0000-000000000000",
            "offer_type": "PLAN_REVIEW",
        },
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 404


def test_create_transaction_returns_404_when_target_is_not_a_dietitian(client: TestClient) -> None:
    buyer_token, _ = register_and_login(client, "txn.buyerplain")
    _, plain_user_id = register_and_login(client, "txn.plaintarget")

    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": plain_user_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 404


def test_create_transaction_rejects_buying_your_own_offer(client: TestClient) -> None:
    token, user_id = register_and_login(client, "txn.self")
    asyncio.run(promote_to_dietitian(user_id))

    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": user_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_create_transaction_rejects_unknown_offer_type(client: TestClient) -> None:
    buyer_token, _ = register_and_login(client, "txn.badoffer")
    _, dietitian_id = register_and_login(client, "txn.badofferdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))

    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "NOT_A_REAL_OFFER"},
        headers=auth_headers(buyer_token),
    )

    assert response.status_code == 422
