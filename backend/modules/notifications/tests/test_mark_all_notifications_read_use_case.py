import uuid

import pytest

from backend.modules.notifications.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)
from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType
from backend.modules.notifications.tests.fakes import InMemoryNotificationRepository


@pytest.mark.asyncio
async def test_execute_marks_all_of_the_recipients_unread_notifications_as_read() -> None:
    repository = InMemoryNotificationRepository()
    recipient_id = uuid.uuid4()
    first = Notification.create(
        recipient_user_id=recipient_id,
        type=NotificationType.NEW_MESSAGE,
        reference_id=uuid.uuid4(),
    )
    second = Notification.create(
        recipient_user_id=recipient_id,
        type=NotificationType.TRANSACTION_PAID,
        reference_id=uuid.uuid4(),
    )
    await repository.save(first)
    await repository.save(second)
    use_case = MarkAllNotificationsReadUseCase(repository)

    results = await use_case.execute(recipient_id)

    assert all(r.read_at is not None for r in results)
    stored = await repository.list_by_recipient(recipient_id)
    assert all(n.read_at is not None for n in stored)


@pytest.mark.asyncio
async def test_execute_does_not_touch_other_recipients_notifications() -> None:
    repository = InMemoryNotificationRepository()
    recipient_id = uuid.uuid4()
    other_recipient_id = uuid.uuid4()
    other = Notification.create(
        recipient_user_id=other_recipient_id,
        type=NotificationType.NEW_MESSAGE,
        reference_id=uuid.uuid4(),
    )
    await repository.save(other)
    use_case = MarkAllNotificationsReadUseCase(repository)

    await use_case.execute(recipient_id)

    stored = await repository.list_by_recipient(other_recipient_id)
    assert stored[0].read_at is None


@pytest.mark.asyncio
async def test_execute_returns_empty_list_when_no_notifications() -> None:
    use_case = MarkAllNotificationsReadUseCase(InMemoryNotificationRepository())

    results = await use_case.execute(uuid.uuid4())

    assert results == []
