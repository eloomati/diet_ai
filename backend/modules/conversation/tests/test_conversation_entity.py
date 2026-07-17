from uuid import uuid4

import pytest

from backend.modules.conversation.domain import (
    ArchivedConversationError,
    Conversation,
    ConversationCategory,
    ConversationCreated,
    ConversationStatus,
    MessageAdded,
    MessageRole,
)


def test_create_conversation_defaults_to_active() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        category=ConversationCategory.BREAKFAST,
    )

    assert conversation.status == ConversationStatus.ACTIVE
    assert conversation.messages == []


def test_create_conversation_adds_created_event() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        category=ConversationCategory.BREAKFAST,
    )

    assert any(isinstance(evt, ConversationCreated) for evt in conversation.domain_events)


def test_add_message_appends_and_adds_event() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        category=ConversationCategory.BREAKFAST,
    )

    message = conversation.add_message(role=MessageRole.USER, content="High protein breakfast?")

    assert conversation.messages == [message]
    assert any(isinstance(evt, MessageAdded) for evt in conversation.domain_events)


def test_archived_conversation_rejects_new_messages() -> None:
    conversation = Conversation.create(
        user_id=uuid4(),
        title="Breakfast ideas",
        category=ConversationCategory.BREAKFAST,
    )
    conversation.archive()

    assert conversation.status == ConversationStatus.ARCHIVED
    with pytest.raises(ArchivedConversationError):
        conversation.add_message(role=MessageRole.USER, content="Still here?")
