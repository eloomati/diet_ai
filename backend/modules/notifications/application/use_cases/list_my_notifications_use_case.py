from uuid import UUID

from backend.modules.notifications.application.dto.notification_dto import NotificationResult
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)


class ListMyNotificationsUseCase:
    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(self, recipient_user_id: UUID) -> list[NotificationResult]:
        notifications = await self._notification_repository.list_by_recipient(recipient_user_id)
        return [NotificationResult.from_domain(n) for n in notifications]
