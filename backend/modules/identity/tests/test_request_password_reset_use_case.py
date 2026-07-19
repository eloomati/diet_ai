import pytest

from backend.modules.identity.application import (
    InvalidCaptchaError,
    RegisterUserCommand,
    RegisterUserUseCase,
)
from backend.modules.identity.application.dto.request_password_reset_dto import (
    RequestPasswordResetCommand,
)
from backend.modules.identity.application.use_cases.request_password_reset_use_case import (
    RequestPasswordResetUseCase,
)
from backend.modules.identity.domain.entities.password_reset_token import PasswordResetToken
from backend.modules.identity.tests.fakes import (
    FakeCaptchaVerifier,
    FakeEmailSender,
    FakePasswordHasher,
    InMemoryEmailVerificationTokenRepository,
    InMemoryPasswordResetTokenRepository,
    InMemoryUserRepository,
)


async def _register(user_repo: InMemoryUserRepository, email: str) -> None:
    # Uses its own throwaway email sender/repo — registration's own verification
    # email is not what these password-reset-focused tests assert on.
    await RegisterUserUseCase(
        user_repo,
        FakePasswordHasher(),
        InMemoryEmailVerificationTokenRepository(),
        FakeEmailSender(),
        FakeCaptchaVerifier(),
    ).execute(
        RegisterUserCommand(email=email, password="StrongPass123", captcha_token="test-captcha-token")
    )


@pytest.mark.asyncio
async def test_request_reset_for_known_email_sends_one_email() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    email_sender = FakeEmailSender()
    await _register(user_repo, "known@example.com")

    use_case = RequestPasswordResetUseCase(user_repo, token_repo, email_sender, FakeCaptchaVerifier())
    await use_case.execute(
        RequestPasswordResetCommand(email="known@example.com", captcha_token="test-captcha-token")
    )

    assert len(email_sender.sent) == 1
    assert email_sender.sent[0].to == "known@example.com"
    assert "Reset token:" in email_sender.sent[0].body


@pytest.mark.asyncio
async def test_request_reset_persists_a_valid_token() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    email_sender = FakeEmailSender()
    await _register(user_repo, "known@example.com")

    use_case = RequestPasswordResetUseCase(user_repo, token_repo, email_sender, FakeCaptchaVerifier())
    await use_case.execute(
        RequestPasswordResetCommand(email="known@example.com", captcha_token="test-captcha-token")
    )

    raw_token = email_sender.sent[0].body.split("Reset token: ")[1].split("\n")[0]
    stored = await token_repo.get_by_token_hash(PasswordResetToken.hash_token(raw_token))
    assert stored is not None
    assert stored.is_valid() is True


@pytest.mark.asyncio
async def test_request_reset_for_unknown_email_sends_no_email() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    email_sender = FakeEmailSender()

    use_case = RequestPasswordResetUseCase(user_repo, token_repo, email_sender, FakeCaptchaVerifier())
    await use_case.execute(
        RequestPasswordResetCommand(email="nobody@example.com", captcha_token="test-captcha-token")
    )

    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_request_reset_for_malformed_email_sends_no_email_and_does_not_raise() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    email_sender = FakeEmailSender()

    use_case = RequestPasswordResetUseCase(user_repo, token_repo, email_sender, FakeCaptchaVerifier())
    await use_case.execute(
        RequestPasswordResetCommand(email="not-an-email", captcha_token="test-captcha-token")
    )

    assert email_sender.sent == []


@pytest.mark.asyncio
async def test_request_reset_with_failed_captcha_raises_before_the_dont_leak_existence_check() -> None:
    user_repo = InMemoryUserRepository()
    token_repo = InMemoryPasswordResetTokenRepository()
    email_sender = FakeEmailSender()
    await _register(user_repo, "known@example.com")

    use_case = RequestPasswordResetUseCase(
        user_repo, token_repo, email_sender, FakeCaptchaVerifier(should_pass=False)
    )

    with pytest.raises(InvalidCaptchaError):
        await use_case.execute(
            RequestPasswordResetCommand(email="known@example.com", captcha_token="bad-token")
        )

    assert email_sender.sent == []
