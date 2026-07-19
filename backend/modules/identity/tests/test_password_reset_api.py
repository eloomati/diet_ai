import re
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.modules.identity.api.dependencies.auth_dependencies import (
    get_captcha_verifier,
    get_email_sender,
)
from backend.modules.identity.tests.fakes import FakeCaptchaVerifier, FakeEmailSender


def unique_email(prefix: str) -> str:
    return f"{prefix}.{uuid.uuid4().hex[:10]}@example.com"


def _extract_reset_token(body: str) -> str:
    match = re.search(r"Reset token: (\S+)", body)
    assert match, f"could not find reset token in email body: {body!r}"
    return match.group(1)


@pytest.fixture
def captured_email_sender():
    sender = FakeEmailSender()
    app.dependency_overrides[get_email_sender] = lambda: sender
    yield sender
    app.dependency_overrides.pop(get_email_sender, None)


@pytest.fixture
def failing_captcha():
    app.dependency_overrides[get_captcha_verifier] = lambda: FakeCaptchaVerifier(should_pass=False)
    yield
    app.dependency_overrides.pop(get_captcha_verifier, None)


def test_request_password_reset_unknown_email_returns_200_and_sends_no_email(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": unique_email("unknown"), "captcha_token": "test-captcha-token"},
    )

    assert response.status_code == 200
    assert captured_email_sender.sent == []


def test_request_password_reset_known_email_returns_200_and_sends_one_email(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("reset.user")
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "captcha_token": "test-captcha-token"},
    )
    assert reg.status_code == 201
    captured_email_sender.sent.clear()  # discard the registration's verification email

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email, "captcha_token": "test-captcha-token"},
    )

    assert response.status_code == 200
    assert len(captured_email_sender.sent) == 1
    assert captured_email_sender.sent[0].purpose == "PASSWORD_RESET"


def test_confirm_password_reset_with_valid_token_changes_password_and_revokes_refresh_tokens(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("reset.confirm")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OldPass123", "captcha_token": "test-captcha-token"},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "OldPass123"})
    old_refresh_token = login.json()["refresh_token"]

    captured_email_sender.sent.clear()
    client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email, "captcha_token": "test-captcha-token"},
    )
    assert len(captured_email_sender.sent) == 1
    raw_token = _extract_reset_token(captured_email_sender.sent[0].body)

    confirm = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "NewPass456"},
    )
    assert confirm.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "OldPass123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewPass456"})
    assert new_login.status_code == 200

    refresh_attempt = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh_token})
    assert refresh_attempt.status_code == 401


def test_confirm_password_reset_with_garbage_token_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": "not-a-real-token", "new_password": "NewPass456"},
    )

    assert response.status_code == 400


def test_confirm_password_reset_with_already_used_token_returns_400(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("reset.reuse")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OldPass123", "captcha_token": "test-captcha-token"},
    )

    captured_email_sender.sent.clear()
    client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email, "captcha_token": "test-captcha-token"},
    )
    raw_token = _extract_reset_token(captured_email_sender.sent[0].body)

    first = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "NewPass456"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "AnotherPass789"},
    )
    assert second.status_code == 400


def test_confirm_password_reset_with_weak_new_password_returns_400(
    client: TestClient, captured_email_sender: FakeEmailSender
) -> None:
    email = unique_email("reset.weak")
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OldPass123", "captcha_token": "test-captcha-token"},
    )

    captured_email_sender.sent.clear()
    client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": email, "captcha_token": "test-captcha-token"},
    )
    raw_token = _extract_reset_token(captured_email_sender.sent[0].body)

    # Long enough to clear the schema's min_length=8, but missing an uppercase
    # letter and a digit — exercises PasswordPolicy inside the use case, not
    # just Pydantic's field validation.
    response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": raw_token, "new_password": "alllowercase"},
    )

    assert response.status_code == 400


def test_request_password_reset_missing_captcha_token_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": unique_email("no.captcha")},
    )
    assert response.status_code == 422


def test_request_password_reset_with_failed_captcha_returns_400(
    client: TestClient, failing_captcha
) -> None:
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": unique_email("bad.captcha"), "captcha_token": "bad-token"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "BAD_REQUEST"
