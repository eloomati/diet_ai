import pytest

from backend.modules.identity.domain import (
    Email,
    InactiveUserAuthenticationError,
    PasswordHash,
    User,
    UserStatus,
)
from backend.modules.identity.domain.events.user_events import (
    PasswordChanged,
    UserLoggedIn,
    UserRegistered,
)


def test_create_user_defaults_to_active() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    assert user.status == UserStatus.ACTIVE


def test_user_create_adds_registered_event() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    assert any(isinstance(evt, UserRegistered) for evt in user.domain_events)


def test_active_user_can_authenticate() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.assert_can_authenticate()


def test_inactive_user_cannot_authenticate() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.deactivate()

    with pytest.raises(InactiveUserAuthenticationError):
        user.assert_can_authenticate()


def test_mark_logged_in_adds_event() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.mark_logged_in()
    assert any(isinstance(evt, UserLoggedIn) for evt in user.domain_events)


def test_change_password_updates_hash_and_adds_event() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    new_hash = PasswordHash("$2b$12$zyxwvutsrqponmlkjihgfe")

    user.change_password(new_hash)

    assert user.password_hash == new_hash
    assert any(isinstance(evt, PasswordChanged) for evt in user.domain_events)