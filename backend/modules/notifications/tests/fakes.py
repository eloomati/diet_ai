from uuid import UUID

from backend.modules.notifications.domain.entities.notification import Notification


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, Notification] = {}

    async def save(self, notification: Notification) -> None:
        self._by_id[notification.id] = notification

    async def list_by_recipient(self, recipient_user_id: UUID) -> list[Notification]:
        notifications = [n for n in self._by_id.values() if n.recipient_user_id == recipient_user_id]
        return sorted(notifications, key=lambda n: n.created_at, reverse=True)
