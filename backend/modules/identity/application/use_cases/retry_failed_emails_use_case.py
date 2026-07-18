from datetime import UTC, datetime

from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.application.use_cases.email_retry_strategies import (
    EmailRetryStrategy,
)
from backend.modules.identity.domain.entities.email_log import (
    DEFAULT_MAX_RETRY_ATTEMPTS,
    DEFAULT_RETRY_INTERVAL_SECONDS,
)
from backend.modules.identity.domain.repositories.email_log_repository import EmailLogRepository
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.email import Email


class RetryFailedEmailsUseCase:
    """Picks up email_logs rows due for a retry and attempts them again. Uses the
    *base* EmailSender, not LoggingEmailSender — this use case owns updating the
    existing log row itself (attempts/status), so wrapping it in the audit decorator
    again would create a second, duplicate row per attempt instead of tracking the
    original one."""

    def __init__(
        self,
        email_log_repository: EmailLogRepository,
        user_repository: UserRepository,
        email_sender: EmailSender,
        strategies: dict[str, EmailRetryStrategy],
        max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
        retry_interval_seconds: int = DEFAULT_RETRY_INTERVAL_SECONDS,
        batch_limit: int = 50,
    ) -> None:
        self._email_log_repository = email_log_repository
        self._user_repository = user_repository
        self._email_sender = email_sender
        self._strategies = strategies
        self._max_attempts = max_attempts
        self._retry_interval_seconds = retry_interval_seconds
        self._batch_limit = batch_limit

    async def execute(self) -> int:
        due = await self._email_log_repository.get_due_for_retry(
            datetime.now(UTC), self._batch_limit
        )
        for log in due:
            try:
                strategy = self._strategies.get(log.purpose)
                if strategy is None:
                    raise ValueError(f"No retry strategy registered for purpose {log.purpose!r}")

                user = await self._user_repository.get_by_email(Email(log.to))
                if user is None:
                    raise ValueError("User no longer exists.")

                subject, body = await strategy.resend(user)
                await self._email_sender.send(to=log.to, subject=subject, body=body, purpose=log.purpose)
            except Exception as exc:
                log.mark_retry_failed(
                    str(exc),
                    max_attempts=self._max_attempts,
                    retry_interval_seconds=self._retry_interval_seconds,
                )
            else:
                log.mark_retry_succeeded()
            await self._email_log_repository.save(log)
        return len(due)
