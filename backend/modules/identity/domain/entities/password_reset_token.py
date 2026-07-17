from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from backend.shared.security import SecureToken


@dataclass(slots=True)
class PasswordResetToken:
    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def issue(cls, user_id: UUID, ttl_minutes: int = 30) -> tuple["PasswordResetToken", str]:
        """Mint a new reset token. Returns (token, raw_token) — raw_token is the only
        time the plaintext secret exists; only its hash is ever persisted."""
        raw_token, token_hash = SecureToken.generate()
        now = datetime.now(UTC)
        token = cls(
            id=uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=ttl_minutes),
            used=False,
            created_at=now,
        )
        return token, raw_token

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return SecureToken.hash(raw_token)

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return current >= self.expires_at

    def is_valid(self, now: datetime | None = None) -> bool:
        return (not self.used) and (not self.is_expired(now))

    def mark_used(self) -> None:
        self.used = True
