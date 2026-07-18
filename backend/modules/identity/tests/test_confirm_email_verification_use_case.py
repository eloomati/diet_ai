from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from backend.modules.identity.application import RegisterUserCommand, RegisterUserUseCase
from backend.modules.identity.application.dto.confirm_email_verification_dto import (
    ConfirmEmailVerificationCommand,
)
from backend.modules.identity.application.use_cases.confirm_email_verification_use_case import (
    ConfirmEmailVerificationUseCase,
)
from backend.modules.identity.domain import InvalidEmailVerificationTokenError
from backend.modules.identity.domain.entities.email_verification_token import (
    EmailVerificationToken,
)
from backend.modules.identity.tests.fakes import (
    FakeEmailSender,
    FakePasswordHasher,
    InMemoryEmailVerificationTokenRepository,
    InMemoryUserRepository,
)


async def _register(user_repo: InMemoryUserRepository, token_repo, email: str) -> UUID:
    result = await RegisterUserUseCase(
        user_repo, FakePasswordHasher(), token_repo, FakeEmailSender()
    ).execute(RegisterUserCommand(email=email, password="StrongPass123"))
    return UUID(result.user_id)


@pytest.mark.asyncio
async def test_confirm_verification_marks_user_verified() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryEmailVerificationTokenRepository()
    user_id = await _register(user_repo, token_repo, "known@example.com")

    # Registration already issued+saved a token; mint a fresh one to control the raw value.
    token, raw_token = EmailVerificationToken.issue(user_id=user_id)
    await token_repo.save(token)

    use_case = ConfirmEmailVerificationUseCase(user_repo, token_repo)
    await use_case.execute(ConfirmEmailVerificationCommand(token=raw_token))

    user = await user_repo.get_by_id(user_id)
    assert user.email_verified is True


@pytest.mark.asyncio
async def test_confirm_verification_marks_token_used() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryEmailVerificationTokenRepository()
    user_id = await _register(user_repo, token_repo, "known@example.com")

    token, raw_token = EmailVerificationToken.issue(user_id=user_id)
    await token_repo.save(token)

    use_case = ConfirmEmailVerificationUseCase(user_repo, token_repo)
    await use_case.execute(ConfirmEmailVerificationCommand(token=raw_token))

    stored = await token_repo.get_by_token_hash(token.token_hash)
    assert stored.used is True


@pytest.mark.asyncio
async def test_confirm_verification_with_unknown_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryEmailVerificationTokenRepository()

    use_case = ConfirmEmailVerificationUseCase(user_repo, token_repo)
    with pytest.raises(InvalidEmailVerificationTokenError):
        await use_case.execute(ConfirmEmailVerificationCommand(token="garbage-token"))


@pytest.mark.asyncio
async def test_confirm_verification_with_expired_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryEmailVerificationTokenRepository()
    user_id = await _register(user_repo, token_repo, "known@example.com")

    token, raw_token = EmailVerificationToken.issue(user_id=user_id)
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await token_repo.save(token)

    use_case = ConfirmEmailVerificationUseCase(user_repo, token_repo)
    with pytest.raises(InvalidEmailVerificationTokenError):
        await use_case.execute(ConfirmEmailVerificationCommand(token=raw_token))


@pytest.mark.asyncio
async def test_confirm_verification_with_already_used_token_raises() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryEmailVerificationTokenRepository()
    user_id = await _register(user_repo, token_repo, "known@example.com")

    token, raw_token = EmailVerificationToken.issue(user_id=user_id)
    token.mark_used()
    await token_repo.save(token)

    use_case = ConfirmEmailVerificationUseCase(user_repo, token_repo)
    with pytest.raises(InvalidEmailVerificationTokenError):
        await use_case.execute(ConfirmEmailVerificationCommand(token=raw_token))
