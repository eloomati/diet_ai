from backend.modules.identity.application.ports.email_sender import EmailSender
from backend.modules.identity.domain.entities.email_log import (
    DEFAULT_MAX_RETRY_ATTEMPTS,
    DEFAULT_RETRY_INTERVAL_SECONDS,
    EmailLog,
)
from backend.modules.identity.domain.repositories.email_log_repository import EmailLogRepository


class LoggingEmailSender(EmailSender):
    """Decorator: records an EmailLog row around any EmailSender send() call.

    Re-raises on failure — the existing propagate-to-500 behavior for a broken
    email send is unchanged, it's now just audited. A failed send is scheduled
    for a background retry (see RetryFailedEmailsUseCase) unless max_attempts is 1."""

    def __init__(
        self,
        inner: EmailSender,
        email_log_repository: EmailLogRepository,
        max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
        retry_interval_seconds: int = DEFAULT_RETRY_INTERVAL_SECONDS,
    ) -> None:
        self._inner = inner
        self._email_log_repository = email_log_repository
        self._max_attempts = max_attempts
        self._retry_interval_seconds = retry_interval_seconds

    async def send(self, to: str, subject: str, body: str, purpose: str) -> None:
        try:
            await self._inner.send(to, subject, body, purpose)
        except Exception as exc:
            await self._email_log_repository.save(
                EmailLog.record_failed(
                    to=to,
                    subject=subject,
                    purpose=purpose,
                    error_message=str(exc),
                    max_attempts=self._max_attempts,
                    retry_interval_seconds=self._retry_interval_seconds,
                )
            )
            raise
        else:
            await self._email_log_repository.save(
                EmailLog.record_sent(to=to, subject=subject, purpose=purpose)
            )
