import uuid

import pytest

from backend.modules.dietitian.domain import (
    DietitianProfile,
    InvalidDietitianProfileError,
    PhotoLimitExceededError,
)


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


def test_add_photo_appends_up_to_three() -> None:
    profile = _create()

    profile.add_photo("/static/dietitian-photos/a.jpg")
    profile.add_photo("/static/dietitian-photos/b.jpg")
    profile.add_photo("/static/dietitian-photos/c.jpg")

    assert profile.photos == (
        "/static/dietitian-photos/a.jpg",
        "/static/dietitian-photos/b.jpg",
        "/static/dietitian-photos/c.jpg",
    )


def test_add_photo_rejects_a_fourth() -> None:
    profile = _create()
    profile.add_photo("/static/dietitian-photos/a.jpg")
    profile.add_photo("/static/dietitian-photos/b.jpg")
    profile.add_photo("/static/dietitian-photos/c.jpg")

    with pytest.raises(PhotoLimitExceededError):
        profile.add_photo("/static/dietitian-photos/d.jpg")
