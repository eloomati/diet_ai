from uuid import uuid4

import pytest

from backend.modules.conversation.application import (
    CreateConversationCommand,
    CreateConversationUseCase,
    ListConversationsQuery,
    ListConversationsUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


@pytest.mark.asyncio
async def test_list_conversations_returns_only_own_conversations() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()
    other_user_id = uuid4()

    await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", categories=["BREAKFAST"])
    )
    await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Leg day", categories=["GYM"])
    )
    await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=other_user_id, title="Someone else's chat", categories=["GENERAL"])
    )

    result = await ListConversationsUseCase(repo).execute(ListConversationsQuery(user_id=user_id))

    assert {r.title for r in result} == {"Breakfast ideas", "Leg day"}


@pytest.mark.asyncio
async def test_list_conversations_empty_for_new_user() -> None:
    repo = InMemoryConversationRepository()

    result = await ListConversationsUseCase(repo).execute(ListConversationsQuery(user_id=uuid4()))

    assert result == []
