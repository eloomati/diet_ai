from datetime import UTC, datetime, timedelta

import pytest

from backend.modules.identity.application.use_cases.email_retry_strategies import (
    EmailVerificationRetryStrategy,
    PasswordResetRetryStrategy,
)
from backend.modules.identity.application.use_cases.retry_failed_emails_use_case import (
    RetryFailedEmailsUseCase,
)
from backend.modules.identity.domain.entities.email_log import EmailDeliveryStatus, EmailLog
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash
from backend.modules.identity.tests.fakes import (
    FailingEmailSender,
    FakeEmailSender,
    InMemoryEmailLogRepository,
    InMemoryEmailVerificationTokenRepository,
    InMemoryPasswordResetTokenRepository,
    InMemoryUserRepository,
)


def _make_user(email: str = "user@example.com") -> User:
    return User.create(email=Email(email), password_hash=PasswordHash("$2b$12$stub"))


def _due_log(purpose: str, to: str = "user@example.com") -> EmailLog:
    log = EmailLog.record_failed(to=to, subject="Subject", purpose=purpose, error_message="boom")
    log.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
    return log


def _build_use_case(email_sender, max_attempts: int = 10):
    user_repo = InMemoryUserRepository()
    log_repo = InMemoryEmailLogRepository()
    reset_repo = InMemoryPasswordResetTokenRepository()
    verify_repo = InMemoryEmailVerificationTokenRepository()
    use_case = RetryFailedEmailsUseCase(
        email_log_repository=log_repo,
        user_repository=user_repo,
        email_sender=email_sender,
        strategies={
            "PASSWORD_RESET": PasswordResetRetryStrategy(reset_repo),
            "EMAIL_VERIFICATION": EmailVerificationRetryStrategy(verify_repo),
        },
        max_attempts=max_attempts,
        retry_interval_seconds=180,
    )
    return use_case, user_repo, log_repo, reset_repo, verify_repo


@pytest.mark.asyncio
async def test_successful_retry_marks_log_sent_and_issues_fresh_token() -> None:
    email_sender = FakeEmailSender()
    use_case, user_repo, log_repo, reset_repo, _ = _build_use_case(email_sender)
    user = _make_user()
    await user_repo.save(user)
    log = _due_log("PASSWORD_RESET", to=user.email.value)
    log_repo.saved.append(log)

    retried = await use_case.execute()

    assert retried == 1
    assert log_repo.saved[0].status == EmailDeliveryStatus.SENT
    assert log_repo.saved[0].next_retry_at is None
    assert len(email_sender.sent) == 1
    assert len(reset_repo._by_hash) == 1


@pytest.mark.asyncio
async def test_repeated_failure_reschedules_until_max_attempts_then_stops() -> None:
    email_sender = FailingEmailSender()
    use_case, user_repo, log_repo, _, _ = _build_use_case(email_sender, max_attempts=3)
    user = _make_user()
    await user_repo.save(user)
    log = _due_log("PASSWORD_RESET", to=user.email.value)
    log_repo.saved.append(log)

    await use_case.execute()
    assert log_repo.saved[0].attempts == 2
    assert log_repo.saved[0].next_retry_at is not None

    log_repo.saved[0].next_retry_at = datetime.now(UTC) - timedelta(seconds=1)
    await use_case.execute()

    assert log_repo.saved[0].attempts == 3
    assert log_repo.saved[0].status == EmailDeliveryStatus.FAILED
    assert log_repo.saved[0].next_retry_at is None

    # Exhausted — no longer due, so a further pass leaves it untouched.
    retried = await use_case.execute()
    assert retried == 0
    assert log_repo.saved[0].attempts == 3


@pytest.mark.asyncio
async def test_deleted_user_fails_retry_with_clear_error() -> None:
    email_sender = FakeEmailSender()
    use_case, _user_repo, log_repo, _, _ = _build_use_case(email_sender)
    log = _due_log("PASSWORD_RESET", to="ghost@example.com")
    log_repo.saved.append(log)

    await use_case.execute()

    assert log_repo.saved[0].status == EmailDeliveryStatus.FAILED
    assert log_repo.saved[0].error_message == "User no longer exists."
    assert len(email_sender.sent) == 0


@pytest.mark.asyncio
async def test_unknown_purpose_fails_retry_with_clear_error() -> None:
    email_sender = FakeEmailSender()
    use_case, user_repo, log_repo, _, _ = _build_use_case(email_sender)
    user = _make_user()
    await user_repo.save(user)
    log = _due_log("SOMETHING_ELSE", to=user.email.value)
    log_repo.saved.append(log)

    await use_case.execute()

    assert log_repo.saved[0].status == EmailDeliveryStatus.FAILED
    assert "No retry strategy registered" in log_repo.saved[0].error_message
