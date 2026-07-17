import dataclasses

import pytest

from backend.modules.conversation.domain import Message, MessageRole


def test_create_message_sets_fields() -> None:
    message = Message.create(role=MessageRole.USER, content="What should I eat today?")

    assert message.role == MessageRole.USER
    assert message.content == "What should I eat today?"
    assert message.token_usage is None
    assert message.id is not None


def test_create_message_with_token_usage() -> None:
    message = Message.create(role=MessageRole.ASSISTANT, content="Try oatmeal.", token_usage=42)

    assert message.token_usage == 42


def test_message_is_immutable() -> None:
    message = Message.create(role=MessageRole.USER, content="Hello")

    with pytest.raises(dataclasses.FrozenInstanceError):
        message.content = "Changed"
