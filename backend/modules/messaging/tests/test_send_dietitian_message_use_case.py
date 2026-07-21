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


@pytest.mark.asyncio
async def test_sender_derived_as_user_when_caller_is_the_buyer() -> None:
    thread_repo = InMemoryDietitianThreadRepository()
    message_repo = InMemoryDietitianMessageRepository()
    thread = DietitianThread.create(user_id=uuid.uuid4(), dietitian_id=uuid.uuid4())
    await thread_repo.save(thread)
    use_case = SendDietitianMessageUseCase(thread_repo, message_repo)

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
    use_case = SendDietitianMessageUseCase(thread_repo, message_repo)

    result = await use_case.execute(
        SendMessageCommand(thread_id=thread.id, caller_id=thread.dietitian_id, content="Hello!")
    )

    assert result.sender == MessageSender.DIETITIAN


@pytest.mark.asyncio
async def test_raises_when_thread_does_not_exist() -> None:
    use_case = SendDietitianMessageUseCase(
        InMemoryDietitianThreadRepository(), InMemoryDietitianMessageRepository()
    )

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
    use_case = SendDietitianMessageUseCase(thread_repo, message_repo)

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
    use_case = SendDietitianMessageUseCase(thread_repo, message_repo)

    with pytest.raises(InvalidMessageError):
        await use_case.execute(
            SendMessageCommand(thread_id=thread.id, caller_id=thread.user_id, content="   ")
        )
