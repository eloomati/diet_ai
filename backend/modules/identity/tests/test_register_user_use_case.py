import pytest

from backend.modules.identity.application import (
    RegisterUserCommand,
    RegisterUserUseCase,
    UserAlreadyExistsError,
)
from backend.modules.identity.tests.fakes import FakePasswordHasher, InMemoryUserRepository


@pytest.mark.asyncio
async def test_register_user_success() -> None:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterUserUseCase(repo, hasher)

    result = await use_case.execute(
        RegisterUserCommand(
            email="new.user@example.com",
            password="StrongPass123",
        )
    )

    assert result.user_id is not None
    assert result.email == "new.user@example.com"


@pytest.mark.asyncio
async def test_register_user_duplicated_email_raises() -> None:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterUserUseCase(repo, hasher)

    await use_case.execute(
        RegisterUserCommand(
            email="dup@example.com",
            password="StrongPass123",
        )
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserCommand(
                email="dup@example.com",
                password="AnotherStrong123",
            )
        )