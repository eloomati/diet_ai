import pytest

from backend.modules.admin.application.use_cases.activate_user_use_case import ActivateUserUseCase
from backend.modules.admin.application.use_cases.ban_user_use_case import BanUserUseCase
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.domain.value_objects.user_status import UserStatus
from backend.modules.identity.tests.fakes import InMemoryUserRepository


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


@pytest.mark.asyncio
async def test_ban_user_sets_status_blocked() -> None:
    repo = InMemoryUserRepository()
    user = User.create(email=Email("ban@example.com"), password_hash=_password_hash())
    await repo.save(user)
    use_case = BanUserUseCase(repo)

    result = await use_case.execute(user.id)

    assert result.status == UserStatus.BLOCKED.value


@pytest.mark.asyncio
async def test_activate_user_sets_status_active() -> None:
    repo = InMemoryUserRepository()
    user = User.create(email=Email("activate@example.com"), password_hash=_password_hash())
    user.block()
    await repo.save(user)
    use_case = ActivateUserUseCase(repo)

    result = await use_case.execute(user.id)

    assert result.status == UserStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_ban_user_raises_when_missing() -> None:
    repo = InMemoryUserRepository()
    use_case = BanUserUseCase(repo)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(User.create(email=Email("x@example.com"), password_hash=_password_hash()).id)


@pytest.mark.asyncio
async def test_activate_user_raises_when_missing() -> None:
    repo = InMemoryUserRepository()
    use_case = ActivateUserUseCase(repo)

    with pytest.raises(UserNotFoundError):
        await use_case.execute(User.create(email=Email("y@example.com"), password_hash=_password_hash()).id)
