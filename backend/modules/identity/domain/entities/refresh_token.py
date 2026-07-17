from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.identity.domain.exceptions.identity_domain_errors import RefreshTokenRevokedError


@dataclass(slots=True)
class RefreshToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def issue(cls, user_id: UUID, token_hash: str, expires_at: datetime) -> "RefreshToken":
        return cls(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked=False,
        )

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return current >= self.expires_at

    def is_active(self, now: datetime | None = None) -> bool:
        return (not self.revoked) and (not self.is_expired(now))

    def revoke(self) -> None:
        self.revoked = True

    def assert_active(self, now: datetime | None = None) -> None:
        if not self.is_active(now):
            raise RefreshTokenRevokedError("Refresh token is revoked or expired.")