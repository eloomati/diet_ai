from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.notifications.application.use_cases.list_my_notifications_use_case import (
    ListMyNotificationsUseCase,
)
from backend.modules.notifications.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from backend.modules.notifications.infrastructure.persistence.repository.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from backend.shared.database import get_db_session


def get_notification_repository(
    session: AsyncSession = Depends(get_db_session),
) -> NotificationRepository:
    return SqlAlchemyNotificationRepository(session)


def get_list_my_notifications_use_case(
    notification_repository: NotificationRepository = Depends(get_notification_repository),
) -> ListMyNotificationsUseCase:
    return ListMyNotificationsUseCase(notification_repository)


def get_mark_all_notifications_read_use_case(
    notification_repository: NotificationRepository = Depends(get_notification_repository),
) -> MarkAllNotificationsReadUseCase:
    return MarkAllNotificationsReadUseCase(notification_repository)
