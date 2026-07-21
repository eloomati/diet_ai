import uuid

import pytest

from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.exceptions.messaging_domain_errors import (
    InvalidMessageError,
)
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender


def test_create_sets_fields() -> None:
    thread_id = uuid.uuid4()
    diet_plan_id = uuid.uuid4()

    message = DietitianMessage.create(
        thread_id=thread_id,
        sender=MessageSender.USER,
        content="Hello!",
        diet_plan_id=diet_plan_id,
    )

    assert message.thread_id == thread_id
    assert message.sender == MessageSender.USER
    assert message.content == "Hello!"
    assert message.diet_plan_id == diet_plan_id


def test_create_defaults_diet_plan_id_to_none() -> None:
    message = DietitianMessage.create(
        thread_id=uuid.uuid4(), sender=MessageSender.DIETITIAN, content="Hi there."
    )

    assert message.diet_plan_id is None


def test_create_rejects_empty_content() -> None:
    with pytest.raises(InvalidMessageError):
        DietitianMessage.create(thread_id=uuid.uuid4(), sender=MessageSender.USER, content="   ")
