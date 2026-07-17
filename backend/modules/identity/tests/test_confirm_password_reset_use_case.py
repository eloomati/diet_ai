from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from backend.modules.identity.application import RegisterUserCommand, RegisterUserUseCase
from backend.modules.identity.application.dto.confirm_password_reset_dto import (
    ConfirmPasswordResetCommand,
)
from backend.modules.identity.application.use_cases.confirm_password_reset_use_case import (
    ConfirmPasswordResetUseCase,
)
from backend.modules.identity.domain import InvalidPasswordError, InvalidPasswordResetTokenError
from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken
from backend.modules.identity.domain.entities.refresh_token import RefreshToken
from backend.modules.identity.tests.fakes import (
    FakePasswordHasher,
    InMemoryPasswordResetTokenRepository,
    InMemoryRefreshTokenRepository,
    InMemoryUserRepository,
)


async def _register(user_repo: InMemoryUserRepository, email: str) -> UUID:
    result = await RegisterUserUseCase(user_repo, FakePasswordHasher()).execute(
        RegisterUserCommand(email=email, password="StrongPass123")
    )
    return UUID(result.user_id)


@pytest.mark.asyncio
async def test_confirm_reset_changes_password_and_marks_token_used() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    user_id = await _register(user_repo, "known@example.com")

    token, raw_token = PasswordResetToken.issue(user_id=user_id)
    await token_repo.save(token)

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    await use_case.execute(
        ConfirmPasswordResetCommand(token=raw_token, new_password="NewStrongPass456")
    )

    user = await user_repo.get_by_id(user_id)
    assert user.password_hash.value == FakePasswordHasher().hash("NewStrongPass456")
    stored_token = await token_repo.get_by_token_hash(token.token_hash)
    assert stored_token.used is True


@pytest.mark.asyncio
async def test_confirm_reset_revokes_all_refresh_tokens_for_user() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    user_id = await _register(user_repo, "known@example.com")

    active_refresh = RefreshToken.issue(
        user_id=user_id,
        token_hash="some-refresh-hash",
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    await refresh_repo.save(active_refresh)

    token, raw_token = PasswordResetToken.issue(user_id=user_id)
    await token_repo.save(token)

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    await use_case.execute(
        ConfirmPasswordResetCommand(token=raw_token, new_password="NewStrongPass456")
    )

    assert await refresh_repo.get_active_by_token_hash("some-refresh-hash") is None


@pytest.mark.asyncio
async def test_confirm_reset_with_unknown_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    with pytest.raises(InvalidPasswordResetTokenError):
        await use_case.execute(
            ConfirmPasswordResetCommand(token="garbage-token", new_password="NewStrongPass456")
        )


@pytest.mark.asyncio
async def test_confirm_reset_with_expired_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    user_id = await _register(user_repo, "known@example.com")

    token, raw_token = PasswordResetToken.issue(user_id=user_id)
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await token_repo.save(token)

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    with pytest.raises(InvalidPasswordResetTokenError):
        await use_case.execute(
            ConfirmPasswordResetCommand(token=raw_token, new_password="NewStrongPass456")
        )


@pytest.mark.asyncio
async def test_confirm_reset_with_already_used_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    user_id = await _register(user_repo, "known@example.com")

    token, raw_token = PasswordResetToken.issue(user_id=user_id)
    token.mark_used()
    await token_repo.save(token)

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    with pytest.raises(InvalidPasswordResetTokenError):
        await use_case.execute(
            ConfirmPasswordResetCommand(token=raw_token, new_password="NewStrongPass456")
        )


@pytest.mark.asyncio
async def test_confirm_reset_rejects_weak_new_password() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    refresh_repo = InMemoryRefreshTokenRepository()
    user_id = await _register(user_repo, "known@example.com")

    token, raw_token = PasswordResetToken.issue(user_id=user_id)
    await token_repo.save(token)

    use_case = ConfirmPasswordResetUseCase(user_repo, token_repo, refresh_repo, FakePasswordHasher())
    with pytest.raises(InvalidPasswordError):
        await use_case.execute(ConfirmPasswordResetCommand(token=raw_token, new_password="weak"))
