import pytest

from backend.modules.identity.domain import (
    DisplayName,
    Email,
    InactiveUserAuthenticationError,
    InvalidDisplayNameError,
    PasswordHash,
    Role,
    User,
    UserStatus,
)
from backend.modules.identity.domain.events.user_events import (
    PasswordChanged,
    UserLoggedIn,
    UserRegistered,
    UserRoleChanged,
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


def test_create_user_defaults_to_role_user() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    assert user.role == Role.USER


def test_change_role_updates_role_and_adds_event() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    user.change_role(Role.DIET_USER)

    assert user.role == Role.DIET_USER
    role_events = [evt for evt in user.domain_events if isinstance(evt, UserRoleChanged)]
    assert len(role_events) == 1
    assert role_events[0].new_role == "DIET_USER"


def test_new_user_has_no_display_name_by_default() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    assert user.display_name is None


def test_set_display_name_updates_it() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    user.set_display_name(DisplayName("Jan Kowalski"))

    assert user.display_name == DisplayName("Jan Kowalski")


def test_set_display_name_to_none_clears_it() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.set_display_name(DisplayName("Jan Kowalski"))

    user.set_display_name(None)

    assert user.display_name is None


def test_display_name_rejects_special_characters() -> None:
    with pytest.raises(InvalidDisplayNameError):
        DisplayName("Jan; DROP TABLE users;")


def test_display_name_strips_surrounding_whitespace() -> None:
    assert DisplayName("  Jan Kowalski  ").value == "Jan Kowalski"


def test_resolved_display_name_falls_back_to_email_when_unset() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )

    assert user.resolved_display_name == "user@example.com"


def test_resolved_display_name_prefers_the_display_name_when_set() -> None:
    user = User.create(
        email=Email("user@example.com"),
        password_hash=PasswordHash("$2b$12$abcdefghijklmnopqrstuv"),
    )
    user.set_display_name(DisplayName("Jan Kowalski"))

    assert user.resolved_display_name == "Jan Kowalski"