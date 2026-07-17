import re
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies.auth_dependencies import get_email_sender
from backend.modules.identity.tests.fakes import FakeEmailSender


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _extract_verification_token(body: str) -> str:
    match = re.search(r"Verification code: (\S+)", body)
    assert match, f"could not find verification code in email body: {body!r}"
    return match.group(1)


@pytest.fixture
def captured_email_sender():
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    yield sender
    app.dependency_overrides.pop(get_email_sender, None)


def test_register_sends_exactly_one_verification_email(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("verify.register")

    response = client.post(
        "/api/v1/auth/register", json={"email": email, "password": "StrongPass123"}
    )

    assert response.status_code == 201
    assert len(captured_email_sender.sent) == 1
    assert captured_email_sender.sent[0].purpose == "EMAIL_VERIFICATION"


def test_confirm_email_verification_with_valid_token_marks_verified(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("verify.confirm")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass123"})
    raw_token = _extract_verification_token(captured_email_sender.sent[0].body)

    login = client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPass123"})
    access_token = login.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {access_token}"}

    before = client.get("/api/v1/auth/me", headers=auth_header)
    assert before.json()["email_verified"] is False

    confirm = client.post("/api/v1/auth/verify-email/confirm", json={"token": raw_token})
    assert confirm.status_code == 200

    after = client.get("/api/v1/auth/me", headers=auth_header)
    assert after.json()["email_verified"] is True


def test_confirm_email_verification_with_garbage_token_returns_400(client: TestClient) -> None:
    response = client.post("/api/v1/auth/verify-email/confirm", json={"token": "garbage"})

    assert response.status_code == 400


def test_confirm_email_verification_with_already_used_token_returns_400(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("verify.reuse")
    client.post("/api/v1/auth/register", json={"email": email, "password": "StrongPass123"})
    raw_token = _extract_verification_token(captured_email_sender.sent[0].body)

    first = client.post("/api/v1/auth/verify-email/confirm", json={"token": raw_token})
    assert first.status_code == 200

    second = client.post("/api/v1/auth/verify-email/confirm", json={"token": raw_token})
    assert second.status_code == 400
