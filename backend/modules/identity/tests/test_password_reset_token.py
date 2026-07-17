from datetime import UTC, datetime, timedelta
from uuid import uuid4

from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken


def test_issue_returns_token_and_raw_secret() -> None:
    token, raw_token = PasswordResetToken.issue(user_id=uuid4())

    assert isinstance(raw_token, str) and len(raw_token) > 20
    assert token.token_hash != raw_token
    assert token.token_hash == PasswordResetToken.hash_token(raw_token)
    assert token.used is False


def test_fresh_token_is_valid() -> None:
    token, _ = PasswordResetToken.issue(user_id=uuid4(), ttl_minutes=30)

    assert token.is_expired() is False
    assert token.is_valid() is True


def test_expired_token_is_invalid() -> None:
    token, _ = PasswordResetToken.issue(user_id=uuid4(), ttl_minutes=30)
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert token.is_expired() is True
    assert token.is_valid() is False


def test_used_token_is_invalid() -> None:
    token, _ = PasswordResetToken.issue(user_id=uuid4())
    token.mark_used()

    assert token.is_valid() is False


def test_hash_token_is_deterministic() -> None:
    assert PasswordResetToken.hash_token("same-input") == PasswordResetToken.hash_token("same-input")


def test_hash_token_differs_for_different_input() -> None:
    assert PasswordResetToken.hash_token("a") != PasswordResetToken.hash_token("b")
