import dataclasses
from datetime import datetime
from uuid import uuid4

import pytest

from backend.modules.identity.domain.events.user_events import UserLoggedIn, UserRegistered


def test_user_registered_event_fields() -> None:
    user_id = uuid4()
    event = UserRegistered(user_id=user_id, email="john@example.com")

    assert event.user_id == user_id
    assert event.email == "john@example.com"
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo is not None


def test_user_logged_in_event_fields() -> None:
    user_id = uuid4()
    event = UserLoggedIn(user_id=user_id)

    assert event.user_id == user_id
    assert isinstance(event.occurred_at, datetime)
    assert event.occurred_at.tzinfo is not None


def test_events_are_immutable() -> None:
    event = UserLoggedIn(user_id=uuid4())

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.user_id = uuid4()