from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from backend.modules.notifications.infrastructure.mappers.notification_mapper import (
    NotificationMapper,
)
from backend.modules.notifications.infrastructure.persistence.models.notification_model import (
    NotificationModel,
)


class SqlAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, notification: Notification) -> None:
        existing = await self._session.get(NotificationModel, notification.id)

        if existing is None:
            model = NotificationMapper.to_model(notification)
            self._session.add(model)
        else:
            # Only `read_at` ever changes after creation (via mark_read()) —
            # listed explicitly per the Etap 0 lesson, not assumed.
            existing.read_at = notification.read_at

        await self._session.flush()

    async def list_by_recipient(self, recipient_user_id: UUID) -> list[Notification]:
        stmt = (
            select(NotificationModel)
            .where(NotificationModel.recipient_user_id == recipient_user_id)
            .order_by(NotificationModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [NotificationMapper.to_domain(model) for model in result.scalars().all()]
