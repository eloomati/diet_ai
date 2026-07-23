from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType


@dataclass(frozen=True, slots=True)
class NotificationResult:
    id: UUID
    recipient_user_id: UUID
    type: NotificationType
    reference_id: UUID
    created_at: datetime
    read_at: datetime | None

    @classmethod
    def from_domain(cls, notification: Notification) -> "NotificationResult":
        return cls(
            id=notification.id,
            recipient_user_id=notification.recipient_user_id,
            type=notification.type,
            reference_id=notification.reference_id,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )
