import asyncio

from fastapi.testclient import TestClient

from backend.modules.admin.tests.db_helpers import auth_headers, promote_role, register_and_login
from backend.modules.identity.domain.value_objects.role import Role


def _create_transaction(client: TestClient, buyer_token: str, dietitian_id: str) -> str:
    response = client.post(
        "/api/v1/transactions",
        json={"dietitian_id": dietitian_id, "offer_type": "PLAN_REVIEW"},
        headers=auth_headers(buyer_token),
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_mark_transaction_paid_requires_admin_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "txn.marknorole")

    response = client.post(
        "/api/v1/admin/transactions/00000000-0000-0000-0000-000000000000/mark-paid",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_admin_marks_transaction_paid_then_unpaid(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "txn.markadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    buyer_token, _ = register_and_login(client, "txn.markbuyer")
    _, dietitian_id = register_and_login(client, "txn.markdietitian")
    asyncio.run(promote_role(dietitian_id, Role.DIET_USER))
    transaction_id = _create_transaction(client, buyer_token, dietitian_id)

    paid_response = client.post(
        f"/api/v1/admin/transactions/{transaction_id}/mark-paid",
        headers=auth_headers(admin_token),
    )
    assert paid_response.status_code == 200
    body = paid_response.json()
    assert body["status"] == "PAID"
    assert body["paid_at"] is not None

    unpaid_response = client.post(
        f"/api/v1/admin/transactions/{transaction_id}/mark-unpaid",
        headers=auth_headers(admin_token),
    )
    assert unpaid_response.status_code == 200
    body = unpaid_response.json()
    assert body["status"] == "UNPAID"
    assert body["paid_at"] is None


def test_mark_transaction_paid_returns_404_for_unknown_transaction(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "txn.mark404")
    asyncio.run(promote_role(admin_id, Role.ADMIN))

    response = client.post(
        "/api/v1/admin/transactions/00000000-0000-0000-0000-000000000000/mark-paid",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_mark_transaction_unpaid_returns_404_for_unknown_transaction(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "txn.markunpaid404")
    asyncio.run(promote_role(admin_id, Role.ADMIN))

    response = client.post(
        "/api/v1/admin/transactions/00000000-0000-0000-0000-000000000000/mark-unpaid",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404
