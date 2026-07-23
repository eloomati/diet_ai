import pytest

from backend.modules.identity.domain import (
    Email,
    InvalidEmailError,
    InvalidPasswordHashError,
    PasswordHash,
    Role,
)


def test_email_normalizes() -> None:
    email = Email("  USER@Example.COM ")
    assert email.value == "user@example.com"


def test_email_invalid() -> None:
    with pytest.raises(InvalidEmailError):
        Email("invalid-email")


def test_password_hash_accepts_bcrypt() -> None:
    h = PasswordHash("$2b$12$abcdefghijklmnopqrstuv")
    assert h.value.startswith("$2")


def test_password_hash_invalid() -> None:
    with pytest.raises(InvalidPasswordHashError):
        PasswordHash("plain-text")


def test_role_has_expected_members() -> None:
    assert {r.value for r in Role} == {"USER", "DIET_USER", "ADMIN", "SUPER_ADMIN"}