from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.messaging.application.use_cases.list_my_dietitian_threads_use_case import (
    ListMyDietitianThreadsUseCase,
)
from backend.modules.messaging.application.use_cases.list_thread_messages_use_case import (
    ListThreadMessagesUseCase,
)
from backend.modules.messaging.application.use_cases.send_dietitian_message_use_case import (
    SendDietitianMessageUseCase,
)
from backend.modules.messaging.domain.repositories.dietitian_message_repository import (
    DietitianMessageRepository,
)
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)
from backend.modules.messaging.infrastructure.persistence.repository.sqlalchemy_dietitian_message_repository import (
    SqlAlchemyDietitianMessageRepository,
)
from backend.modules.messaging.infrastructure.persistence.repository.sqlalchemy_dietitian_thread_repository import (
    SqlAlchemyDietitianThreadRepository,
)
from backend.modules.notifications.api.dependencies import get_notification_repository
from backend.modules.notifications.application.use_cases.create_notification_use_case import (
    CreateNotificationUseCase,
)
from backend.modules.notifications.domain.repositories.notification_repository import (
    NotificationRepository,
)
from backend.shared.database import get_db_session


def get_dietitian_thread_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DietitianThreadRepository:
    return SqlAlchemyDietitianThreadRepository(session)


def get_dietitian_message_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DietitianMessageRepository:
    return SqlAlchemyDietitianMessageRepository(session)


def get_user_repository_for_messaging(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_list_my_dietitian_threads_use_case(
    thread_repository: DietitianThreadRepository = Depends(get_dietitian_thread_repository),
    user_repository: UserRepository = Depends(get_user_repository_for_messaging),
) -> ListMyDietitianThreadsUseCase:
    return ListMyDietitianThreadsUseCase(thread_repository, user_repository)


def get_list_thread_messages_use_case(
    thread_repository: DietitianThreadRepository = Depends(get_dietitian_thread_repository),
    message_repository: DietitianMessageRepository = Depends(get_dietitian_message_repository),
) -> ListThreadMessagesUseCase:
    return ListThreadMessagesUseCase(thread_repository, message_repository)


def get_create_notification_use_case_for_messaging(
    notification_repository: NotificationRepository = Depends(get_notification_repository),
) -> CreateNotificationUseCase:
    return CreateNotificationUseCase(notification_repository)


def get_send_dietitian_message_use_case(
    thread_repository: DietitianThreadRepository = Depends(get_dietitian_thread_repository),
    message_repository: DietitianMessageRepository = Depends(get_dietitian_message_repository),
    create_notification_use_case: CreateNotificationUseCase = Depends(
        get_create_notification_use_case_for_messaging
    ),
) -> SendDietitianMessageUseCase:
    return SendDietitianMessageUseCase(
        thread_repository, message_repository, create_notification_use_case
    )
