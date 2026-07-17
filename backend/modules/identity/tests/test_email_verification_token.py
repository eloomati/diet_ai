from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)


def test_issue_returns_token_and_raw_secret() -> None:
    token, raw_token = EmailVerificationToken.issue(user_id=uuid4())

    assert isinstance(raw_token, str) and len(raw_token) > 20
    assert token.token_hash != raw_token
    assert token.used is False


def test_fresh_token_is_valid() -> None:
    token, _ = EmailVerificationToken.issue(user_id=uuid4())

    assert token.is_expired() is False
    assert token.is_valid() is True


def test_expired_token_is_invalid() -> None:
    token, _ = EmailVerificationToken.issue(user_id=uuid4())
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert token.is_expired() is True
    assert token.is_valid() is False


def test_used_token_is_invalid() -> None:
    token, _ = EmailVerificationToken.issue(user_id=uuid4())
    token.mark_used()

    assert token.is_valid() is False


def test_default_ttl_is_24_hours() -> None:
    token, _ = EmailVerificationToken.issue(user_id=uuid4())

    expected = datetime.now(UTC) + timedelta(hours=24)
    assert abs((token.expires_at - expected).total_seconds()) < 5
