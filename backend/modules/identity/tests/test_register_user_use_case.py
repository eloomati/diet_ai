import pytest

from backend.modules.identity.application import (
    RegisterUserCommand,
    RegisterUserUseCase,
    UserAlreadyExistsError,
)
from backend.modules.identity.tests.fakes import (
    FakeEmailSender,
    FakePasswordHasher,
    InMemoryEmailVerificationTokenRepository,
    InMemoryUserRepository,
)


@pytest.mark.asyncio
async def test_register_user_success() -> None:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    email_sender = FakeEmailSender()
    use_case = RegisterUserUseCase(
        repo, hasher, InMemoryEmailVerificationTokenRepository(), email_sender
    )

    result = await use_case.execute(
        RegisterUserCommand(
            email="new.user@example.com",
            password="StrongPass123",
        )
    )

    assert result.user_id is not None
    assert result.email == "new.user@example.com"


@pytest.mark.asyncio
async def test_register_user_sends_verification_email() -> None:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    email_sender = FakeEmailSender()
    verification_repo = InMemoryEmailVerificationTokenRepository()
    use_case = RegisterUserUseCase(repo, hasher, verification_repo, email_sender)

    await use_case.execute(
        RegisterUserCommand(email="new.user@example.com", password="StrongPass123")
    )

    assert len(email_sender.sent) == 1
    assert email_sender.sent[0].to == "new.user@example.com"
    assert email_sender.sent[0].purpose == "EMAIL_VERIFICATION"
    assert "Verification code:" in email_sender.sent[0].body


@pytest.mark.asyncio
async def test_register_user_duplicated_email_raises() -> None:
    repo = InMemoryUserRepository()
    hasher = FakePasswordHasher()
    use_case = RegisterUserUseCase(
        repo, hasher, InMemoryEmailVerificationTokenRepository(), FakeEmailSender()
    )

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