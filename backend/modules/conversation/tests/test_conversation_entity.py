from uuid import uuid4

import pytest

from backend.modules.conversation.domain import (
    ArchivedConversationError,
    Conversation,
    ConversationCategory,
    ConversationCreated,
    ConversationStatus,
    InvalidConversationError,
    MessageAdded,
    MessageRole,
)


def test_create_conversation_defaults_to_active() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        categories=[ConversationCategory.BREAKFAST],
    )

    assert conversation.status == ConversationStatus.ACTIVE
    assert conversation.messages == []


def test_create_conversation_adds_created_event() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        categories=[ConversationCategory.BREAKFAST],
    )

    assert any(isinstance(evt, ConversationCreated) for evt in conversation.domain_events)


def test_add_message_appends_and_adds_event() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        categories=[ConversationCategory.BREAKFAST],
    )

    message = conversation.add_message(role=MessageRole.USER, content="High protein breakfast?")

    assert conversation.messages == [message]
    assert any(isinstance(evt, MessageAdded) for evt in conversation.domain_events)


def test_create_conversation_with_multiple_categories() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Cutting + race prep",
        categories=[ConversationCategory.DIET, ConversationCategory.RUNNING],
    )

    assert conversation.categories == (ConversationCategory.DIET, ConversationCategory.RUNNING)


def test_create_conversation_deduplicates_repeated_categories() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        categories=[ConversationCategory.BREAKFAST, ConversationCategory.BREAKFAST],
    )

    assert conversation.categories == (ConversationCategory.BREAKFAST,)


def test_create_conversation_requires_at_least_one_category() -> None:
    with pytest.raises(InvalidConversationError):
        Conversation.create(user_id=uuid4(), title="Breakfast ideas", categories=[])


def test_archived_conversation_rejects_new_messages() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        categories=[ConversationCategory.BREAKFAST],
    )
    conversation.archive()

    assert conversation.status == ConversationStatus.ARCHIVED
    with pytest.raises(ArchivedConversationError):
        conversation.add_message(role=MessageRole.USER, content="Still here?")
