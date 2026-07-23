import uuid

import pytest

from backend.modules.messaging.application.use_cases.exceptions import (
    ThreadAccessDeniedError,
    ThreadNotFoundError,
)
from backend.modules.messaging.application.use_cases.list_thread_messages_use_case import (
    ListThreadMessagesUseCase,
)
from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender
from backend.modules.messaging.tests.fakes import (
    InMemoryDietitianMessageRepository,
    InMemoryDietitianThreadRepository,
)


@pytest.mark.asyncio
async def test_returns_messages_in_chronological_order() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    first = DietitianMessage.create(thread_id=thread.id, sender=MessageSender.USER, content="Hi")
    second = DietitianMessage.create(
        thread_id=thread.id, sender=MessageSender.DIETITIAN, content="Hello!"
    )
    await message_repo.save(first)
    await message_repo.save(second)
    use_case = ListThreadMessagesUseCase(thread_repo, message_repo)

    results = await use_case.execute(thread.id, thread.user_id)

    assert [r.content for r in results] == ["Hi", "Hello!"]


@pytest.mark.asyncio
async def test_raises_when_thread_does_not_exist() -> None:
    use_case = ListThreadMessagesUseCase(
        InMemoryDietitianThreadRepository(), InMemoryDietitianMessageRepository()
    )

    with pytest.raises(ThreadNotFoundError):
        await use_case.execute(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_raises_when_caller_is_not_a_participant() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = ListThreadMessagesUseCase(thread_repo, message_repo)

    with pytest.raises(ThreadAccessDeniedError):
        await use_case.execute(thread.id, uuid.uuid4())
