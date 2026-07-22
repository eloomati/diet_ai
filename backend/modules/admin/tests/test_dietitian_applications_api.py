import asyncio

from fastapi.testclient import TestClient

from backend.modules.admin.tests.db_helpers import auth_headers, promote_role, register_and_login
from backend.modules.identity.domain.value_objects.role import Role

_APPLICATION_PAYLOAD = {
    "experience": "5 years as a clinical dietitian",
    "diplomas": ["MSc Dietetics"],
    "description": "Weight management specialist.",
}


def test_list_dietitian_applications_requires_admin_role(client: TestClient) -> None:
    token, _ = register_and_login(client, "admin.applistnorole")

    response = client.get("/api/v1/admin/dietitian-applications", headers=auth_headers(token))

    assert response.status_code == 403


def test_approve_dietitian_application_promotes_user(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.approveadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    applicant_token, applicant_id = register_and_login(client, "admin.approveapplicant")
    submit = client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=auth_headers(applicant_token),
    )
    application_id = submit.json()["id"]

    response = client.post(
        f"/api/v1/admin/dietitian-applications/{application_id}/approve",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"

    me_response = client.get("/api/v1/auth/me", headers=auth_headers(applicant_token))
    assert me_response.json()["role"] == "DIET_USER"

    profile_response = client.get(
        "/api/v1/dietitian/profile/me", headers=auth_headers(applicant_token)
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["experience"] == _APPLICATION_PAYLOAD["experience"]


def test_reject_dietitian_application_does_not_promote_user(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.rejectadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    applicant_token, _ = register_and_login(client, "admin.rejectapplicant")
    submit = client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=auth_headers(applicant_token),
    )
    application_id = submit.json()["id"]

    response = client.post(
        f"/api/v1/admin/dietitian-applications/{application_id}/reject",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"

    me_response = client.get("/api/v1/auth/me", headers=auth_headers(applicant_token))
    assert me_response.json()["role"] == "USER"


def test_approve_twice_returns_409(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.twiceadmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    applicant_token, _ = register_and_login(client, "admin.twiceapplicant")
    submit = client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=auth_headers(applicant_token),
    )
    application_id = submit.json()["id"]
    client.post(
        f"/api/v1/admin/dietitian-applications/{application_id}/approve",
        headers=auth_headers(admin_token),
    )

    response = client.post(
        f"/api/v1/admin/dietitian-applications/{application_id}/approve",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 409


def test_list_dietitian_applications_filters_by_status(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.filteradmin")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    applicant_token, _ = register_and_login(client, "admin.filterapplicant")
    client.post(
        "/api/v1/dietitian/applications",
        json=_APPLICATION_PAYLOAD,
        headers=auth_headers(applicant_token),
    )

    response = client.get(
        "/api/v1/admin/dietitian-applications",
        params={"status": "PENDING"},
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    body = response.json()
    assert all(a["status"] == "PENDING" for a in body["items"])
    assert body["total"] == len(body["items"])


def test_list_dietitian_applications_paginates_with_limit_and_offset(client: TestClient) -> None:
    admin_token, admin_id = register_and_login(client, "admin.appPaginate")
    asyncio.run(promote_role(admin_id, Role.ADMIN))
    for suffix in ("a", "b", "c"):
        applicant_token, _ = register_and_login(client, f"admin.appPaginate.{suffix}")
        client.post(
            "/api/v1/dietitian/applications",
            json=_APPLICATION_PAYLOAD,
            headers=auth_headers(applicant_token),
        )

    full = client.get(
        "/api/v1/admin/dietitian-applications",
        params={"status": "PENDING"},
        headers=auth_headers(admin_token),
    ).json()
    assert full["total"] >= 3

    page = client.get(
        "/api/v1/admin/dietitian-applications",
        params={"status": "PENDING", "limit": 2, "offset": 0},
        headers=auth_headers(admin_token),
    ).json()

    assert len(page["items"]) == 2
    assert page["total"] == full["total"]
