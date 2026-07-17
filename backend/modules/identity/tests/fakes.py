from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.identity.domain.entities.email_log import EmailLog
from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)
from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken
from backend.modules.identity.domain.entities.refresh_token import RefreshToken
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email


@dataclass(frozen=True, slots=True)
class FakeTokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, User] = {}
        self._by_email: dict[str, User] = {}

    async def get_by_id(self, user_id: UUID) -> User | None:
        return self._by_id.get(user_id)

    async def get_by_email(self, email: Email) -> User | None:
        return self._by_email.get(email.value)

    async def exists_by_email(self, email: Email) -> bool:
        return email.value in self._by_email

    async def save(self, user: User) -> None:
        self._by_id[user.id] = user
        self._by_email[user.email.value] = user


class InMemoryRefreshTokenRepository:
    def __init__(self) -> None:
        self._by_hash: dict[str, RefreshToken] = {}

    async def save(self, refresh_token: RefreshToken) -> None:
        self._by_hash[refresh_token.token_hash] = refresh_token

    async def get_active_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        token = self._by_hash.get(token_hash)
        if token is None:
            return None
        if token.revoked or token.is_expired(datetime.now(UTC)):
            return None
        return token

    async def revoke(self, token_id: UUID) -> None:
        for token in self._by_hash.values():
            if token.id == token_id:
                token.revoke()
                return

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        for token in self._by_hash.values():
            if token.user_id == user_id:
                token.revoke()


class InMemoryPasswordResetTokenRepository:
    def __init__(self) -> None:
        self._by_hash: dict[str, PasswordResetToken] = {}

    async def save(self, token: PasswordResetToken) -> None:
        self._by_hash[token.token_hash] = token

    async def get_by_token_hash(self, token_hash: str) -> PasswordResetToken | None:
        return self._by_hash.get(token_hash)


class InMemoryEmailVerificationTokenRepository:
    def __init__(self) -> None:
        self._by_hash: dict[str, EmailVerificationToken] = {}

    async def save(self, token: EmailVerificationToken) -> None:
        self._by_hash[token.token_hash] = token

    async def get_by_token_hash(self, token_hash: str) -> EmailVerificationToken | None:
        return self._by_hash.get(token_hash)


class InMemoryEmailLogRepository:
    def __init__(self) -> None:
        self.saved: list[EmailLog] = []

    async def save(self, log: EmailLog) -> None:
        for index, existing in enumerate(self.saved):
            if existing.id == log.id:
                self.saved[index] = log
                return
        self.saved.append(log)

    async def get_due_for_retry(self, now: datetime, limit: int = 50) -> list[EmailLog]:
        due = [log for log in self.saved if log.is_due_for_retry(now)]
        return due[:limit]


@dataclass
class SentEmail:
    to: str
    subject: str
    body: str
    purpose: str = ""


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send(self, to: str, subject: str, body: str, purpose: str = "") -> None:
        self.sent.append(SentEmail(to=to, subject=subject, body=body, purpose=purpose))


class FailingEmailSender:
    """Always raises — for exercising retry/failure paths without a real inner sender."""

    def __init__(self, error_message: str = "SMTP connection refused") -> None:
        self.error_message = error_message
        self.attempts = 0

    async def send(self, to: str, subject: str, body: str, purpose: str = "") -> None:
        self.attempts += 1
        raise RuntimeError(self.error_message)


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"$2b$12${plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"$2b$12${plain_password}"


class FakeTokenService:
    def create_access_token(self, user_id: str, email: str) -> str:
        return f"access::{user_id}::{email}"

    # WAŻNE: musi rotować, żeby test refresh flow przechodził (new != old)
    def create_refresh_token(self, user_id: str) -> str:
        return f"refresh::{user_id}::{uuid4()}"

    def decode_refresh_token(self, token: str) -> dict[str, str]:
        # format: refresh::<user_id>::<nonce>
        parts = token.split("::")
        if len(parts) != 3 or parts[0] != "refresh":
            raise ValueError("Invalid refresh token format.")
        return {"sub": parts[1]}