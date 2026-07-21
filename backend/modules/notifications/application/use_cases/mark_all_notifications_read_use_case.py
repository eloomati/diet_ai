from uuid import UUID

from backend.modules.notifications.application.dto.notification_dto import NotificationResult
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)


class MarkAllNotificationsReadUseCase:
    """One bulk action, not per-notification mark-read — a demo-scope
    user has few enough notifications that "mark everything I can
    currently see as read" is the only action the small badge UI needs."""

    def __init__(self, notification_repository: NotificationRepository) -> None:
        self._notification_repository = notification_repository

    async def execute(self, recipient_user_id: UUID) -> list[NotificationResult]:
        notifications = await self._notification_repository.list_by_recipient(recipient_user_id)
        for notification in notifications:
            if notification.read_at is None:
                notification.mark_read()
                await self._notification_repository.save(notification)
        return [NotificationResult.from_domain(n) for n in notifications]
