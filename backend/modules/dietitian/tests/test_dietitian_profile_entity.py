import uuid

import pytest

from backend.modules.dietitian.domain import DietitianProfile, InvalidDietitianProfileError


def _create(**overrides) -> DietitianProfile:
    defaults = dict(
        user_id=uuid.uuid4(),
        experience="5 years as a clinical dietitian",
        diplomas=("MSc Nutrition, University X",),
        description="I help clients build sustainable eating habits.",
    )
    defaults.update(overrides)
    return DietitianProfile.create(**defaults)


def test_create_rejects_empty_experience() -> None:
    with pytest.raises(InvalidDietitianProfileError):
        _create(experience="")


def test_create_rejects_empty_description() -> None:
    with pytest.raises(InvalidDietitianProfileError):
        _create(description="   ")


def test_update_details_changes_only_given_fields() -> None:
    profile = _create()
    original_diplomas = profile.diplomas

    profile.update_details(description="Updated description.")

    assert profile.description == "Updated description."
    assert profile.diplomas == original_diplomas
    assert profile.experience == "5 years as a clinical dietitian"


def test_update_details_rejects_blanking_out_experience() -> None:
    profile = _create()

    with pytest.raises(InvalidDietitianProfileError):
        profile.update_details(experience="   ")
