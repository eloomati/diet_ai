from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.conversation.application import (
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    GetConversationHistoryQuery,
    GetConversationHistoryUseCase,
    SendMessageCommand,
    SendMessageUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


@pytest.mark.asyncio
async def test_get_conversation_history_returns_messages() -> None:
    repo = InMemoryConversationRepository()
    user_id = uuid4()

    created = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", category="BREAKFAST")
    )
    conversation_id = UUID(created.conversation_id)

    await SendMessageUseCase(repo, FakeLLMProvider(canned_response="Try oatmeal.")).execute(
        SendMessageCommand(conversation_id=conversation_id, user_id=user_id, content="Hi")
    )

    result = await GetConversationHistoryUseCase(repo).execute(
        GetConversationHistoryQuery(conversation_id=conversation_id, user_id=user_id)
    )

    assert result.title == "Breakfast ideas"
    assert result.category == "BREAKFAST"
    assert len(result.messages) == 2
    assert result.messages[0].role == "USER"
    assert result.messages[1].role == "ASSISTANT"


@pytest.mark.asyncio
async def test_get_conversation_history_for_non_owner_raises() -> None:
    repo = InMemoryConversationRepository()
    owner_id = uuid4()

    created = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=owner_id, title="Leg day", category="GYM")
    )
    conversation_id = UUID(created.conversation_id)

    with pytest.raises(ConversationNotFoundError):
        await GetConversationHistoryUseCase(repo).execute(
            GetConversationHistoryQuery(conversation_id=conversation_id, user_id=uuid4())
        )
