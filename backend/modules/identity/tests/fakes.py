from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

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