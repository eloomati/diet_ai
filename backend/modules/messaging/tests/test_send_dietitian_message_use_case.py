import uuid

import pytest

from backend.modules.messaging.application.dto.messaging_dto import SendMessageCommand
from backend.modules.messaging.application.use_cases.exceptions import (
    ThreadAccessDeniedError,
    ThreadNotFoundError,
)
from backend.modules.messaging.application.use_cases.send_dietitian_message_use_case import (
    SendDietitianMessageUseCase,
)
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.domain.exceptions.messaging_domain_errors import (
    InvalidMessageError,
)
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender
from backend.modules.messaging.tests.fakes import (
    InMemoryDietitianMessageRepository,
    InMemoryDietitianThreadRepository,
)
from backend.modules.notifications.application.use_cases.create_notification_use_case import (
    CreateNotificationUseCase,
)
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType
from backend.modules.notifications.tests.fakes import InMemoryNotificationRepository


def _use_case(
    thread_repo: InMemoryDietitianThreadRepository,
    message_repo: InMemoryDietitianMessageRepository,
    notification_repo: InMemoryNotificationRepository | None = None,
) -> SendDietitianMessageUseCase:
    notification_repo = notification_repo or InMemoryNotificationRepository()
    return SendDietitianMessageUseCase(
        thread_repo, message_repo, CreateNotificationUseCase(notification_repo)
    )


@pytest.mark.asyncio
async def test_sender_derived_as_user_when_caller_is_the_buyer() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, message_repo)

    result = await use_case.execute(
        SendMessageCommand(thread_id=thread.id, caller_id=thread.user_id, content="Hi")
    )

    assert result.sender == MessageSender.USER


@pytest.mark.asyncio
async def test_sender_derived_as_dietitian_when_caller_is_the_dietitian() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, message_repo)

    result = await use_case.execute(
        SendMessageCommand(thread_id=thread.id, caller_id=thread.dietitian_id, content="Hello!")
    )

    assert result.sender == MessageSender.DIETITIAN


@pytest.mark.asyncio
async def test_raises_when_thread_does_not_exist() -> None:
    use_case = _use_case(InMemoryDietitianThreadRepository(), InMemoryDietitianMessageRepository())

    with pytest.raises(ThreadNotFoundError):
        await use_case.execute(
            SendMessageCommand(thread_id=uuid.uuid4(), caller_id=uuid.uuid4(), content="Hi")
        )


@pytest.mark.asyncio
async def test_raises_when_caller_is_not_a_participant() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, message_repo)

    with pytest.raises(ThreadAccessDeniedError):
        await use_case.execute(
            SendMessageCommand(thread_id=thread.id, caller_id=uuid.uuid4(), content="Hi")
        )


@pytest.mark.asyncio
async def test_raises_when_content_is_blank() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, message_repo)

    with pytest.raises(InvalidMessageError):
        await use_case.execute(
            SendMessageCommand(thread_id=thread.id, caller_id=thread.user_id, content="   ")
        )


@pytest.mark.asyncio
async def test_notifies_the_other_participant_when_a_message_is_sent() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    notification_repo = InMemoryNotificationRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = _use_case(thread_repo, message_repo, notification_repo)

    await use_case.execute(
        SendMessageCommand(thread_id=thread.id, caller_id=thread.user_id, content="Hi")
    )

    notifications = await notification_repo.list_by_recipient(thread.dietitian_id)
    assert len(notifications) == 1
    assert notifications[0].type == NotificationType.NEW_MESSAGE
    assert notifications[0].reference_id == thread.id
