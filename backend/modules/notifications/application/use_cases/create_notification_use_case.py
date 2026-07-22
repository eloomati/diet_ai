from uuid import UUID

from backend.modules.notifications.application.dto.notification_dto import NotificationResult
from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType


class CreateNotificationUseCase:
    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(
        self, recipient_user_id: UUID, type: NotificationType, reference_id: UUID
    ) -> NotificationResult:
        notification = Notification.create(
            recipient_user_id=recipient_user_id, type=type, reference_id=reference_id
        )
        await self._notification_repository.save(notification)
        return NotificationResult.from_domain(notification)
