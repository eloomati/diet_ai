from uuid import uuid4

from backend.modules.ai.application import PromptBuilder
from backend.modules.ai.domain import PromptTurn
from backend.modules.conversation.domain import Conversation, ConversationCategory, MessageRole


def test_prompt_builder_uses_conversation_category() -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )

    prompt = PromptBuilder.build(conversation, question="What should I eat?")

    assert prompt.category == "BREAKFAST"
    assert prompt.question == "What should I eat?"
    assert prompt.conversation_history == ()


def test_prompt_builder_includes_prior_history_but_not_current_question() -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )
    conversation.add_message(role=MessageRole.USER, content="Hi")
    conversation.add_message(role=MessageRole.ASSISTANT, content="Hello, how can I help?")

    prompt = PromptBuilder.build(conversation, question="What should I eat?")

    assert prompt.conversation_history == (
        PromptTurn(role="user", content="Hi"),
        PromptTurn(role="assistant", content="Hello, how can I help?"),
    )
    assert prompt.question == "What should I eat?"
