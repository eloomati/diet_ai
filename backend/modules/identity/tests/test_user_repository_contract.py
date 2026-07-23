from uuid import UUID

import pytest

from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash


class InMemoryUserRepository(UserRepository):
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

    async def list_all(self, limit: int | None = None, offset: int = 0) -> list[User]:
        users = list(self._by_id.values())[offset:]
        return users[:limit] if limit is not None else users

    async def count_all(self) -> int:
        return len(self._by_id)

    async def delete(self, user_id: UUID) -> None:
        user = self._by_id.pop(user_id, None)
        if user is not None:
            self._by_email.pop(user.email.value, None)


@pytest.mark.asyncio
async def test_repository_save_and_get_by_email() -> None:
    repo = InMemoryUserRepository()
    user = User.create(
        email=Email("repo@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    await repo.save(user)
    found = await repo.get_by_email(Email("repo@example.com"))

    assert found is not None
    assert found.id == user.id


@pytest.mark.asyncio
async def test_repository_exists_by_email() -> None:
    repo = InMemoryUserRepository()
    user = User.create(
        email=Email("exists@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    await repo.save(user)

    assert await repo.exists_by_email(Email("exists@example.com")) is True
    assert await repo.exists_by_email(Email("missing@example.com")) is False


@pytest.mark.asyncio
async def test_repository_get_by_email_returns_none_when_missing() -> None:
    repo = InMemoryUserRepository()

    found = await repo.get_by_email(Email("nobody@example.com"))

    assert found is None