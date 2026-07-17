from dataclasses import dataclass
from uuid import UUID

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


class FakePasswordHasher:
    def hash(self, plain_password: str) -> str:
        return f"$2b$12${plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return password_hash == f"$2b$12${plain_password}"


class FakeTokenService:
    def create_access_token(self, *, user_id: str, email: str) -> str:
        return f"access::{user_id}::{email}"

    def create_refresh_token(self, *, user_id: str) -> str:
        return f"refresh::{user_id}"

    def issue_pair(self, *, user_id: str, email: str) -> FakeTokenPair:
        return FakeTokenPair(
            access_token=self.create_access_token(user_id=user_id, email=email),
            refresh_token=self.create_refresh_token(user_id=user_id),
            token_type="bearer",
        )