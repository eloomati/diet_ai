from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from backend.modules.identity.domain.entities.refresh_token import RefreshToken
from backend.modules.identity.domain.exceptions.identity_domain_errors import RefreshTokenRevokedError


def test_issue_refresh_token_active() -> None:
    token = RefreshToken.issue(
        user_id=uuid4(),
        token_hash="hashed_token",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    assert token.revoked is False
    assert token.is_expired() is False
    assert token.is_active() is True


def test_revoked_token_is_not_active() -> None:
    token = RefreshToken.issue(
        user_id=uuid4(),
        token_hash="hashed_token",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    token.revoke()
    assert token.is_active() is False

    with pytest.raises(RefreshTokenRevokedError):
        token.assert_active()


def test_expired_token_is_not_active() -> None:
    token = RefreshToken.issue(
        user_id=uuid4(),
        token_hash="hashed_token",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    assert token.is_active() is False

    with pytest.raises(RefreshTokenRevokedError):
        token.assert_active()