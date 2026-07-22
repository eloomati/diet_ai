from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.notifications.application.dto.notification_dto import NotificationResult
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType


class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationType
    reference_id: UUID
    created_at: datetime
    read_at: datetime | None

    @classmethod
    def from_result(cls, result: NotificationResult) -> "NotificationResponse":
        return cls(
            id=result.id,
            type=result.type,
            reference_id=result.reference_id,
            created_at=result.created_at,
            read_at=result.read_at,
        )
