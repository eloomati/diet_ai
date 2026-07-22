import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.nutrition.api.dependencies.diet_plan_dependencies import get_sftp_client
from backend.modules.nutrition.tests.fakes import FakeSftpClient


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient, prefix: str) -> str:
    email = unique_email(prefix)
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


_PROFILE_PAYLOAD = {
    "age": 29,
    "height_cm": 187,
    "weight_kg": 80,
    "activity_level": "HIGH",
    "goal": "MUSCLE_GAIN",
    "diet_type": "VEGETARIAN",
}


@pytest.fixture
def captured_sftp_client():
    # A shared instance, unlike the real per-request get_sftp_client — so an
    # export in one request and a download in a later request within the same
    # test can see the same uploaded files (see FakeSftpClient's docstring).
    sftp = FakeSftpClient()
    app.dependency_overrides[get_sftp_client] = lambda: sftp
    yield sftp
    app.dependency_overrides.pop(get_sftp_client, None)


def _create_plan(client: TestClient, token: str, prefix: str) -> str:
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    created = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    ).json()
    return created["plan_id"]


def test_export_diet_plan_returns_201_and_metadata(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.create")
    plan_id = _create_plan(client, token, "export.create")

    response = client.post(f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(token))

    assert response.status_code == 201
    body = response.json()
    assert body["diet_plan_id"] == plan_id
    assert body["filename"] in captured_sftp_client.files
    assert b"Mock meal" in captured_sftp_client.files[body["filename"]]


def test_export_unknown_plan_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.unknown")

    response = client.post(
        "/api/v1/diet-plans/00000000-0000-0000-0000-000000000000/export",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_export_other_users_plan_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    owner_token = _register_and_login(client, "export.owner")
    other_token = _register_and_login(client, "export.other")
    plan_id = _create_plan(client, owner_token, "export.owner")

    response = client.post(
        f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(other_token)
    )

    assert response.status_code == 404


def test_list_diet_plan_exports_returns_previous_exports(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.list")
    plan_id = _create_plan(client, token, "export.list")
    client.post(f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(token))
    client.post(f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(token))

    response = client.get(f"/api/v1/diet-plans/{plan_id}/exports", headers=_auth_headers(token))

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_diet_plan_exports_empty_before_any_export(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.listempty")
    plan_id = _create_plan(client, token, "export.listempty")

    response = client.get(f"/api/v1/diet-plans/{plan_id}/exports", headers=_auth_headers(token))

    assert response.status_code == 200
    assert response.json() == []


def test_download_diet_plan_export_returns_the_csv(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.download")
    plan_id = _create_plan(client, token, "export.download")
    exported = client.post(
        f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(token)
    ).json()

    response = client.get(
        f"/api/v1/diet-plans/{plan_id}/exports/{exported['export_id']}/download",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert b"Mock meal" in response.content
    assert response.content.splitlines()[0] == b"day_number,date,time,meal_name,calories,protein,carbohydrates,fat"


def test_download_unknown_export_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.downloadunknown")
    plan_id = _create_plan(client, token, "export.downloadunknown")

    response = client.get(
        f"/api/v1/diet-plans/{plan_id}/exports/00000000-0000-0000-0000-000000000000/download",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_export_combined_diet_plans_saves_without_downloading(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.combined")
    client.post("/api/v1/profile", json=_PROFILE_PAYLOAD, headers=_auth_headers(token))
    plan_a = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    ).json()
    plan_b = client.post(
        "/api/v1/diet-plans/generate", json={"duration_days": 1}, headers=_auth_headers(token)
    ).json()

    response = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": [plan_a["plan_id"], plan_b["plan_id"]]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["diet_plan_ids"] == [plan_a["plan_id"], plan_b["plan_id"]]
    assert body["filename"] in captured_sftp_client.files
    csv_text = captured_sftp_client.files[body["filename"]].decode("utf-8")
    assert csv_text.count("Mock meal") == 2
    assert plan_a["plan_id"] in csv_text
    assert plan_b["plan_id"] in csv_text


def test_download_combined_diet_plan_export_returns_the_saved_csv(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.combined.download")
    plan_id = _create_plan(client, token, "export.combined.download")
    saved = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": [plan_id]},
        headers=_auth_headers(token),
    ).json()

    response = client.get(
        f"/api/v1/diet-plans/exports-combined/{saved['export_id']}/download",
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.splitlines()[0] == (
        b"plan_id,day_number,date,time,meal_name,calories,protein,carbohydrates,fat"
    )
    assert b"Mock meal" in response.content


def test_download_combined_diet_plan_export_unknown_export_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.combined.dlunknown")

    response = client.get(
        "/api/v1/diet-plans/exports-combined/00000000-0000-0000-0000-000000000000/download",
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_download_combined_diet_plan_export_other_users_export_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    owner_token = _register_and_login(client, "export.combined.dlowner")
    other_token = _register_and_login(client, "export.combined.dlother")
    plan_id = _create_plan(client, owner_token, "export.combined.dlowner")
    saved = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": [plan_id]},
        headers=_auth_headers(owner_token),
    ).json()

    response = client.get(
        f"/api/v1/diet-plans/exports-combined/{saved['export_id']}/download",
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 404


def test_export_combined_diet_plans_rejects_an_empty_plan_id_list(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.combined.empty")

    response = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": []},
        headers=_auth_headers(token),
    )

    assert response.status_code == 422


def test_export_combined_diet_plans_unknown_plan_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    token = _register_and_login(client, "export.combined.unknown")
    plan_id = _create_plan(client, token, "export.combined.unknown")

    response = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": [plan_id, "00000000-0000-0000-0000-000000000000"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


def test_export_combined_diet_plans_other_users_plan_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    owner_token = _register_and_login(client, "export.combined.owner")
    other_token = _register_and_login(client, "export.combined.other")
    owner_plan_id = _create_plan(client, owner_token, "export.combined.owner")
    other_plan_id = _create_plan(client, other_token, "export.combined.other")

    response = client.post(
        "/api/v1/diet-plans/export-combined",
        json={"plan_ids": [owner_plan_id, other_plan_id]},
        headers=_auth_headers(owner_token),
    )

    assert response.status_code == 404


def test_download_other_users_export_returns_404(
    client: TestClient, captured_sftp_client: FakeSftpClient
) -> None:
    owner_token = _register_and_login(client, "export.dl.owner")
    other_token = _register_and_login(client, "export.dl.other")
    plan_id = _create_plan(client, owner_token, "export.dl.owner")
    exported = client.post(
        f"/api/v1/diet-plans/{plan_id}/export", headers=_auth_headers(owner_token)
    ).json()

    response = client.get(
        f"/api/v1/diet-plans/{plan_id}/exports/{exported['export_id']}/download",
        headers=_auth_headers(other_token),
    )

    assert response.status_code == 404
