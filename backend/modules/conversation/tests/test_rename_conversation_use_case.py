from uuid import UUID, uuid4

import pytest

from backend.modules.conversation.application import (
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    RenameConversationCommand,
    RenameConversationUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


async def _create_conversation(repo: InMemoryConversationRepository, user_id) -> UUID:
    result = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", categories=["BREAKFAST"])
    )
    return UUID(result.conversation_id)


@pytest.mark.asyncio
async def test_rename_conversation_changes_title() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    result = await RenameConversationUseCase(repo).execute(
        RenameConversationCommand(conversation_id=conversation_id, user_id=user_id, title="Dinner ideas")
    )

    assert result.title == "Dinner ideas"


@pytest.mark.asyncio
async def test_renamed_conversation_persists() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    await RenameConversationUseCase(repo).execute(
        RenameConversationCommand(conversation_id=conversation_id, user_id=user_id, title="Dinner ideas")
    )

    stored = await repo.get_by_id(conversation_id)
    assert stored.title == "Dinner ideas"


@pytest.mark.asyncio
async def test_rename_unknown_conversation_raises() -> None:
    repo = InMemoryConversationRepository()

    with pytest.raises(ConversationNotFoundError):
        await RenameConversationUseCase(repo).execute(
            RenameConversationCommand(conversation_id=uuid4(), user_id=uuid4(), title="New title")
        )


@pytest.mark.asyncio
async def test_rename_from_non_owner_raises() -> None:
    repo = InMemoryConversationRepository()
    owner_id = uuid4()
    conversation_id = await _create_conversation(repo, owner_id)

    with pytest.raises(ConversationNotFoundError):
        await RenameConversationUseCase(repo).execute(
            RenameConversationCommand(conversation_id=conversation_id, user_id=uuid4(), title="Sneaky")
        )
