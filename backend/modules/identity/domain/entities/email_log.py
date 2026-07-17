from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

DEFAULT_MAX_RETRY_ATTEMPTS = 10
DEFAULT_RETRY_INTERVAL_SECONDS = 180


class EmailDeliveryStatus(StrEnum):
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass(slots=True)
class EmailLog:
    id: UUID
    to: str
    subject: str
    purpose: str
    status: EmailDeliveryStatus
    attempts: int = 1
    next_retry_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def record_sent(cls, to: str, subject: str, purpose: str) -> "EmailLog":
        return cls(id=uuid4(), to=to, subject=subject, purpose=purpose, status=EmailDeliveryStatus.SENT)

    @classmethod
    def record_failed(
        cls,
        to: str,
        subject: str,
        purpose: str,
        error_message: str,
        max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
        retry_interval_seconds: int = DEFAULT_RETRY_INTERVAL_SECONDS,
    ) -> "EmailLog":
        next_retry_at = (
            datetime.now(UTC) + timedelta(seconds=retry_interval_seconds) if max_attempts > 1 else None
        )
        return cls(
            id=uuid4(),
            to=to,
            subject=subject,
            purpose=purpose,
            status=EmailDeliveryStatus.FAILED,
            attempts=1,
            next_retry_at=next_retry_at,
            error_message=error_message,
        )

    def is_due_for_retry(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        return (
            self.status == EmailDeliveryStatus.FAILED
            and self.next_retry_at is not None
            and current >= self.next_retry_at
        )

    def mark_retry_succeeded(self) -> None:
        self.status = EmailDeliveryStatus.SENT
        self.error_message = None
        self.next_retry_at = None

    def mark_retry_failed(
        self,
        error_message: str,
        max_attempts: int = DEFAULT_MAX_RETRY_ATTEMPTS,
        retry_interval_seconds: int = DEFAULT_RETRY_INTERVAL_SECONDS,
    ) -> None:
        self.attempts += 1
        self.error_message = error_message
        if self.attempts >= max_attempts:
            # Attempts exhausted — stop scheduling further retries. Status stays
            # FAILED, which is already the case; this just stops get_due_for_retry
            # from picking the row up again.
            self.next_retry_at = None
        else:
            self.next_retry_at = datetime.now(UTC) + timedelta(seconds=retry_interval_seconds)
