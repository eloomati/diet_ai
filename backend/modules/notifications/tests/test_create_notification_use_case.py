import uuid

import pytest

from backend.modules.notifications.application.use_cases.create_notification_use_case import (
    CreateNotificationUseCase,
)
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType
from backend.modules.notifications.tests.fakes import InMemoryNotificationRepository


@pytest.mark.asyncio
async def test_execute_creates_and_saves_a_notification() -> None:
    repository = InMemoryNotificationRepository()
    use_case = CreateNotificationUseCase(repository)
    recipient_id = uuid.uuid4()
    reference_id = uuid.uuid4()

    result = await use_case.execute(
        recipient_user_id=recipient_id,
        type=NotificationType.TRANSACTION_PAID,
        reference_id=reference_id,
    )

    assert result.recipient_user_id == recipient_id
    assert result.type == NotificationType.TRANSACTION_PAID
    assert result.reference_id == reference_id
    assert result.read_at is None

    stored = await repository.list_by_recipient(recipient_id)
    assert [n.id for n in stored] == [result.id]
