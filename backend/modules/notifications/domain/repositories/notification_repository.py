from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.notifications.domain.entities.notification import Notification


class NotificationRepository(ABC):
    @abstractmethod
    async def save(self, notification: Notification) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_recipient(self, recipient_user_id: UUID) -> list[Notification]:
        raise NotImplementedError
