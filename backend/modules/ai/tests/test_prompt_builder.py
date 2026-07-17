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


def test_prompt_builder_includes_nutrition_framing_and_category_guidance() -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Creatine?", category=ConversationCategory.SUPPLEMENTS
    )

    prompt = PromptBuilder.build(conversation, question="Should I take creatine?")

    assert "nutrition" in prompt.system_prompt.lower()
    assert "supplement" in prompt.system_prompt.lower()


def test_prompt_builder_uses_distinct_guidance_per_category() -> None:
    breakfast = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )
    running = Conversation.create(user_id=uuid4(), title="Race prep", category=ConversationCategory.RUNNING)

    breakfast_prompt = PromptBuilder.build(breakfast, question="What should I eat?")
    running_prompt = PromptBuilder.build(running, question="What should I eat before a race?")

    assert breakfast_prompt.system_prompt != running_prompt.system_prompt
    assert "breakfast" in breakfast_prompt.system_prompt.lower()
    assert "endurance" in running_prompt.system_prompt.lower()


def test_prompt_builder_folds_in_user_profile_when_given() -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )

    prompt = PromptBuilder.build(
        conversation,
        question="What should I eat?",
        user_profile="28yo, 75kg, goal: muscle gain",
    )

    assert "75kg" in prompt.system_prompt


def test_prompt_builder_omits_user_profile_line_when_not_given() -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )

    prompt = PromptBuilder.build(conversation, question="What should I eat?")

    assert "User profile:" not in prompt.system_prompt
