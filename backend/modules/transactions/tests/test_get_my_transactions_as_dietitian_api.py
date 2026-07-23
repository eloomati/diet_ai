import asyncio

from fastapi.testclient import TestClient

from backend.modules.transactions.tests.db_helpers import (
    auth_headers,
    mark_transaction_paid_directly,
    promote_to_dietitian,
    register_and_login,
    verify_email,
)


def test_get_my_transactions_requires_diet_user_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "txn.mynorole")

    response = client.get("/api/v1/transactions/me", headers=auth_headers(token))

    assert response.status_code == 403


def test_get_my_transactions_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/transactions/me")

    assert response.status_code == 401


def test_get_my_transactions_returns_only_own_transactions(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "txn.mybuyer")
    dietitian_token, dietitian_id = register_and_login(client, "txn.mydietitian")
    asyncio.run(promote_to_dietitian(dietitian_id))
    _, other_dietitian_id = register_and_login(client, "txn.otherdietitian")
    asyncio.run(promote_to_dietitian(other_dietitian_id))
    asyncio.run(verify_email(buyer_id))

    client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )
    client.post(
        "/api/v1/transactions",
        json={"dietitian_id": other_dietitian_id, "offer_type": "INDIVIDUAL_PLAN"},
        headers=auth_headers(buyer_token),
    )

    response = client.get("/api/v1/transactions/me", headers=auth_headers(dietitian_token))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["dietitian_id"] == dietitian_id
    assert body[0]["offer_type"] == "PLAN_REVIEW"


def test_get_my_transactions_reveals_buyer_email_once_paid(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "txn.revealbuyer")
    dietitian_token, dietitian_id = register_and_login(client, "txn.revealdiet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    asyncio.run(verify_email(buyer_id))

    created = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    ).json()
    asyncio.run(mark_transaction_paid_directly(created["id"]))

    response = client.get("/api/v1/transactions/me", headers=auth_headers(dietitian_token))

    assert response.status_code == 200
    body = response.json()
    assert body[0]["status"] == "PAID"
    assert body[0]["buyer_email"] is not None
    assert "@" in body[0]["buyer_email"]


def test_get_my_transactions_hides_buyer_email_while_unpaid(client: TestClient) -> None:
    buyer_token, buyer_id = register_and_login(client, "txn.hidebuyer")
    dietitian_token, dietitian_id = register_and_login(client, "txn.hidediet")
    asyncio.run(promote_to_dietitian(dietitian_id))
    asyncio.run(verify_email(buyer_id))

    client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )

    response = client.get("/api/v1/transactions/me", headers=auth_headers(dietitian_token))

    assert response.status_code == 200
    body = response.json()
    assert body[0]["status"] == "UNPAID"
    assert body[0]["buyer_email"] is None
