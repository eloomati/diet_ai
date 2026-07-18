from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.conversation.application import (
    ArchiveConversationCommand,
    ArchiveConversationUseCase,
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    SendMessageCommand,
    SendMessageUseCase,
)
from backend.modules.conversation.domain import ArchivedConversationError
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository
from backend.modules.nutrition.tests.fakes import InMemoryNutritionProfileRepository


async def _create_conversation(repo: InMemoryConversationRepository, user_id) -> UUID:
    result = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", categories=["BREAKFAST"])
    )
    return UUID(result.conversation_id)


@pytest.mark.asyncio
async def test_archive_conversation_sets_status_archived() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    result = await ArchiveConversationUseCase(repo).execute(
        ArchiveConversationCommand(conversation_id=conversation_id, user_id=user_id)
    )

    assert result.status == "ARCHIVED"


@pytest.mark.asyncio
async def test_archived_conversation_persists() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    await ArchiveConversationUseCase(repo).execute(
        ArchiveConversationCommand(conversation_id=conversation_id, user_id=user_id)
    )

    stored = await repo.get_by_id(conversation_id)
    assert stored.status.value == "ARCHIVED"


@pytest.mark.asyncio
async def test_archived_conversation_rejects_new_messages() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)
    await ArchiveConversationUseCase(repo).execute(
        ArchiveConversationCommand(conversation_id=conversation_id, user_id=user_id)
    )

    use_case = SendMessageUseCase(repo, FakeLLMProvider(), InMemoryNutritionProfileRepository())
    with pytest.raises(ArchivedConversationError):
        await use_case.execute(
            SendMessageCommand(conversation_id=conversation_id, user_id=user_id, content="Hi")
        )


@pytest.mark.asyncio
async def test_archive_unknown_conversation_raises() -> None:
    repo = InMemoryConversationRepository()

    with pytest.raises(ConversationNotFoundError):
        await ArchiveConversationUseCase(repo).execute(
            ArchiveConversationCommand(conversation_id=uuid4(), user_id=uuid4())
        )


@pytest.mark.asyncio
async def test_archive_from_non_owner_raises() -> None:
    repo = InMemoryConversationRepository()
    owner_id = uuid4()
    conversation_id = await _create_conversation(repo, owner_id)

    with pytest.raises(ConversationNotFoundError):
        await ArchiveConversationUseCase(repo).execute(
            ArchiveConversationCommand(conversation_id=conversation_id, user_id=uuid4())
        )
