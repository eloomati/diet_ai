from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.conversation.application import (
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    SendMessageCommand,
    SendMessageUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


async def _create_conversation(repo: InMemoryConversationRepository, user_id: UUID) -> UUID:
    result = await CreateConversationUseCase(repo).execute(
        CreateConversationCommand(user_id=user_id, title="Breakfast ideas", category="BREAKFAST")
    )
    return UUID(result.conversation_id)


@pytest.mark.asyncio
async def test_send_message_returns_ai_response() -> None:
    repo = InMemoryConversationRepository()
    llm = FakeLLMProvider(canned_response="Try oatmeal with berries.")
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    use_case = SendMessageUseCase(repo, llm)
    result = await use_case.execute(
        SendMessageCommand(
            conversation_id=conversation_id,
            user_id=user_id,
            content="What should I eat for breakfast?",
        )
    )

    assert result.assistant_content == "Try oatmeal with berries."
    assert result.user_message_id != result.assistant_message_id


@pytest.mark.asyncio
async def test_send_message_persists_both_messages() -> None:
    repo = InMemoryConversationRepository()
    llm = FakeLLMProvider(canned_response="Try oatmeal.")
    user_id = uuid4()
    conversation_id = await _create_conversation(repo, user_id)

    await SendMessageUseCase(repo, llm).execute(
        SendMessageCommand(conversation_id=conversation_id, user_id=user_id, content="Hi")
    )

    stored = await repo.get_by_id(conversation_id)
    assert len(stored.messages) == 2
    assert stored.messages[0].content == "Hi"
    assert stored.messages[1].content == "Try oatmeal."


@pytest.mark.asyncio
async def test_send_message_to_unknown_conversation_raises() -> None:
    repo = InMemoryConversationRepository()
    llm = FakeLLMProvider()
    use_case = SendMessageUseCase(repo, llm)

    with pytest.raises(ConversationNotFoundError):
        await use_case.execute(
            SendMessageCommand(conversation_id=uuid4(), user_id=uuid4(), content="Hi")
        )


@pytest.mark.asyncio
async def test_send_message_from_non_owner_raises() -> None:
    repo = InMemoryConversationRepository()
    llm = FakeLLMProvider()
    owner_id = uuid4()
    conversation_id = await _create_conversation(repo, owner_id)

    use_case = SendMessageUseCase(repo, llm)
    with pytest.raises(ConversationNotFoundError):
        await use_case.execute(
            SendMessageCommand(conversation_id=conversation_id, user_id=uuid4(), content="Hi")
        )
