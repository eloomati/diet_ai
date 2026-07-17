from uuid import UUID, uuid4

import pytest

from backend.modules.conversation.application import (
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    DeleteConversationCommand,
    DeleteConversationUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


async def _create_conversation(repo: InMemoryConversationRepository, user_id) -> UUID:
    result = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", category="BREAKFAST")
    )
    return UUID(result.conversation_id)


@pytest.mark.asyncio
async def test_delete_conversation_removes_it() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    await DeleteConversationUseCase(repo).execute(
        DeleteConversationCommand(conversation_id=conversation_id, user_id=user_id)
    )

    assert await repo.get_by_id(conversation_id) is None


@pytest.mark.asyncio
async def test_delete_unknown_conversation_raises() -> None:
    repo = InMemoryConversationRepository()

    with pytest.raises(ConversationNotFoundError):
        await DeleteConversationUseCase(repo).execute(
            DeleteConversationCommand(conversation_id=uuid4(), user_id=uuid4())
        )


@pytest.mark.asyncio
async def test_delete_from_non_owner_raises_and_keeps_conversation() -> None:
    repo = InMemoryConversationRepository()
    owner_id = uuid4()
    conversation_id = await _create_conversation(repo, owner_id)

    with pytest.raises(ConversationNotFoundError):
        await DeleteConversationUseCase(repo).execute(
            DeleteConversationCommand(conversation_id=conversation_id, user_id=uuid4())
        )

    assert await repo.get_by_id(conversation_id) is not None
