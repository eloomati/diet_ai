import uuid

import pytest

from backend.modules.notifications.application.use_cases.list_my_notifications_use_case import (
    ListMyNotificationsUseCase,
)
from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType
from backend.modules.notifications.tests.fakes import InMemoryNotificationRepository


@pytest.mark.asyncio
async def test_execute_returns_only_the_recipients_own_notifications() -> None:
    repository = InMemoryNotificationRepository()
    recipient_id = uuid.uuid4()
    mine = Notification.create(
        recipient_user_id=recipient_id,
        type=NotificationType.NEW_MESSAGE,
        reference_id=uuid.uuid4(),
    )
    someone_elses = Notification.create(
        recipient_user_id=uuid.uuid4(),
        type=NotificationType.NEW_MESSAGE,
        reference_id=uuid.uuid4(),
    )
    await repository.save(mine)
    await repository.save(someone_elses)
    use_case = ListMyNotificationsUseCase(repository)

    results = await use_case.execute(recipient_id)

    assert [r.id for r in results] == [mine.id]


@pytest.mark.asyncio
async def test_execute_returns_empty_list_when_no_notifications() -> None:
    use_case = ListMyNotificationsUseCase(InMemoryNotificationRepository())

    results = await use_case.execute(uuid.uuid4())

    assert results == []
