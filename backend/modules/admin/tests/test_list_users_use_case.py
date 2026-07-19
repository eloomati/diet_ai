import pytest

from backend.modules.admin.application.use_cases.list_users_use_case import ListUsersUseCase
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.tests.fakes import InMemoryUserRepository


@pytest.mark.asyncio
async def test_list_users_returns_all_users() -> None:
    repo = InMemoryUserRepository()
    await repo.save(
        User.create(email=Email("a@example.com"), password_hash=PasswordHash("$2b$12$" + "a" * 22))
    )
    await repo.save(
        User.create(email=Email("b@example.com"), password_hash=PasswordHash("$2b$12$" + "b" * 22))
    )
    use_case = ListUsersUseCase(repo)

    results = await use_case.execute()

    assert {r.email for r in results} == {"a@example.com", "b@example.com"}
    assert all(r.role == "USER" for r in results)


@pytest.mark.asyncio
async def test_list_users_returns_empty_list_when_none() -> None:
    repo = InMemoryUserRepository()
    use_case = ListUsersUseCase(repo)

    assert await use_case.execute() == []
