import uuid

from backend.modules.dietitian.application.services.resolve_dietitian_name import (
    resolve_dietitian_name,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.identity.domain.entities.user import User
from backend.modules.identity.domain.value_objects.display_name import DisplayName
from backend.modules.identity.domain.value_objects.email import Email
from backend.modules.identity.domain.value_objects.password_hash import PasswordHash


def _password_hash() -> PasswordHash:
    return PasswordHash("$2b$12$" + "a" * 22)


def _profile(**overrides) -> DietitianProfile:
    defaults = dict(
        user_id=uuid.uuid4(),
        experience="5 years",
        diplomas=(),
        description="Description.",
    )
    defaults.update(overrides)
    return DietitianProfile.create(**defaults)


def test_prefers_the_real_name_when_both_first_and_last_are_set() -> None:
    user = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    user.set_display_name(DisplayName("DietNick"))
    profile = _profile(first_name="Jan", last_name="Kowalski")

    assert resolve_dietitian_name(profile, user) == "Jan Kowalski"


def test_falls_back_to_display_name_when_only_one_of_first_last_is_set() -> None:
    user = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    user.set_display_name(DisplayName("DietNick"))
    profile = _profile(first_name="Jan", last_name=None)

    assert resolve_dietitian_name(profile, user) == "DietNick"


def test_falls_back_to_display_name_when_neither_name_is_set() -> None:
    user = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    user.set_display_name(DisplayName("DietNick"))
    profile = _profile()

    assert resolve_dietitian_name(profile, user) == "DietNick"


def test_falls_back_to_email_when_nothing_else_is_set() -> None:
    user = User.create(email=Email("dietitian@example.com"), password_hash=_password_hash())
    profile = _profile()

    assert resolve_dietitian_name(profile, user) == "dietitian@example.com"
