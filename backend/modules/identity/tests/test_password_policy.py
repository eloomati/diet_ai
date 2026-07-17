import pytest

from backend.modules.identity.domain import InvalidPasswordError, PasswordPolicy


def test_password_policy_accepts_strong_password() -> None:
    PasswordPolicy.validate("StrongPass123")


def test_password_policy_rejects_short_password() -> None:
    with pytest.raises(InvalidPasswordError):
        PasswordPolicy.validate("S1a!")


def test_password_policy_rejects_missing_uppercase() -> None:
    with pytest.raises(InvalidPasswordError):
        PasswordPolicy.validate("strongpass123")


def test_password_policy_rejects_missing_digit() -> None:
    with pytest.raises(InvalidPasswordError):
        PasswordPolicy.validate("StrongPassword")