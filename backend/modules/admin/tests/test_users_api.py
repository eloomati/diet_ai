import asyncio

from fastapi.testclient import TestClient

from backend.modules.admin.tests.db_helpers import auth_headers, promote_role, register_and_login
from backend.modules.identity.domain.value_objects.role import Role


def test_list_users_requires_admin_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "admin.listnorole")

    response = client.get("/api/v1/admin/users", headers=auth_headers(token))

    assert response.status_code == 403


def test_list_users_returns_all_users(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.list")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    register_and_login(client, "admin.listtarget")

    response = client.get("/api/v1/admin/users", headers=auth_headers(admin_token))

    assert response.status_code == 200
    body = response.json()
    emails = [u["email"] for u in body["items"]]
    assert any("admin.listtarget" in email for email in emails)
    assert body["total"] == len(body["items"])


def test_ban_then_activate_user(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.banadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    _, target_id = register_and_login(client, "admin.bantarget")

    ban_response = client.post(
        f"/api/v1/admin/users/{target_id}/ban", headers=auth_headers(admin_token)
    )
    assert ban_response.status_code == 200
    assert ban_response.json()["status"] == "BLOCKED"

    activate_response = client.post(
        f"/api/v1/admin/users/{target_id}/activate", headers=auth_headers(admin_token)
    )
    assert activate_response.status_code == 200
    assert activate_response.json()["status"] == "ACTIVE"


def test_ban_user_returns_404_for_unknown_user(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.ban404")
    asyncio.run(promote_role(admin_id, Role.ADMIN))

    response = client.post(
        "/api/v1/admin/users/00000000-0000-0000-0000-000000000000/ban",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_delete_user_removes_them_from_the_list(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.deleteadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    _, target_id = register_and_login(client, "admin.deletetarget")

    response = client.delete(f"/api/v1/admin/users/{target_id}", headers=auth_headers(admin_token))

    assert response.status_code == 204
    list_response = client.get("/api/v1/admin/users", headers=auth_headers(admin_token))
    assert all(u["id"] != target_id for u in list_response.json()["items"])


def test_delete_user_rejects_deleting_self(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.deleteself")
    asyncio.run(promote_role(admin_id, Role.ADMIN))

    response = client.delete(f"/api/v1/admin/users/{admin_id}", headers=auth_headers(admin_token))

    assert response.status_code == 400


def test_list_users_paginates_with_limit_and_offset(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.paginate")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    register_and_login(client, "admin.paginate.a")
    register_and_login(client, "admin.paginate.b")
    register_and_login(client, "admin.paginate.c")

    full = client.get("/api/v1/admin/users", headers=auth_headers(admin_token)).json()
    total = full["total"]
    assert total >= 4

    first_page = client.get(
        "/api/v1/admin/users",
        params={"limit": 2, "offset": 0},
        headers=auth_headers(admin_token),
    ).json()
    second_page = client.get(
        "/api/v1/admin/users",
        params={"limit": 2, "offset": 2},
        headers=auth_headers(admin_token),
    ).json()

    assert len(first_page["items"]) == 2
    assert first_page["total"] == total
    assert second_page["total"] == total
    first_ids = {u["id"] for u in first_page["items"]}
    second_ids = {u["id"] for u in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)
