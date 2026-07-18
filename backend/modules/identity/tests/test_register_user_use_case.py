import pytest

from backend.modules.identity.application import (
    InvalidCaptchaError,
    RegisterUserCommand,
    RegisterUserUseCase,
    UserAlreadyExistsError,
)
from backend.modules.identity.domain import Email
from backend.modules.identity.tests.fakes import (
    FakeCaptchaVerifier,
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
        repo,
        hasher,
        InMemoryEmailVerificationTokenRepository(),
        email_sender,
        FakeCaptchaVerifier(),
    )

    result = await use_case.execute(
        RegisterUserCommand(
            email="new.user@example.com",
            password="StrongPass123",
            captcha_token="test-captcha-token",
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
    use_case = RegisterUserUseCase(
        repo, hasher, verification_repo, email_sender, FakeCaptchaVerifier()
    )

    await use_case.execute(
        RegisterUserCommand(
            email="new.user@example.com",
            password="StrongPass123",
            captcha_token="test-captcha-token",
        )
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
        repo,
        hasher,
        InMemoryEmailVerificationTokenRepository(),
        FakeEmailSender(),
        FakeCaptchaVerifier(),
    )

    await use_case.execute(
        RegisterUserCommand(
            email="dup@example.com",
            password="StrongPass123",
            captcha_token="test-captcha-token",
        )
    )

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            RegisterUserCommand(
                email="dup@example.com",
                password="AnotherStrong123",
                captcha_token="test-captcha-token",
            )
        )


@pytest.mark.asyncio
async def test_register_user_with_failed_captcha_raises_before_touching_the_repository() -> None:
    repo = InMemoryUserRepository()
    use_case = RegisterUserUseCase(
        repo,
        FakePasswordHasher(),
        InMemoryEmailVerificationTokenRepository(),
        FakeEmailSender(),
        FakeCaptchaVerifier(should_pass=False),
    )

    with pytest.raises(InvalidCaptchaError):
        await use_case.execute(
            RegisterUserCommand(
                email="new.user@example.com",
                password="StrongPass123",
                captcha_token="bad-token",
            )
        )

    assert await repo.exists_by_email(Email("new.user@example.com")) is False
