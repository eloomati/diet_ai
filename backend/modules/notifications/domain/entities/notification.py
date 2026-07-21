from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.notifications.domain.value_objects.notification_type import NotificationType


@dataclass(slots=True)
class Notification:
    id: UUID
    recipient_user_id: UUID
    type: NotificationType
    # Points at a different table depending on `type` (a transaction id for
    # TRANSACTION_PAID, a thread id for the future NEW_MESSAGE) — a
    # polymorphic reference, so it carries no FK constraint of its own.
    reference_id: UUID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None

    @classmethod
    def create(
        cls, recipient_user_id: UUID, type: NotificationType, reference_id: UUID
    ) -> "Notification":
        return cls(
            id=uuid4(),
            recipient_user_id=recipient_user_id,
            type=type,
            reference_id=reference_id,
            created_at=datetime.now(UTC),
        )

    def mark_read(self) -> None:
        # Idempotent, same spirit as Transaction's mark_paid()/mark_unpaid()
        # — re-marking an already-read notification read is a no-op state,
        # not an error.
        self.read_at = datetime.now(UTC)
