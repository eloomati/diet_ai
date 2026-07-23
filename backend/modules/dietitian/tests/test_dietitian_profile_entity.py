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


def test_remove_photo_drops_the_given_index() -> None:
    profile = _create()
    profile.add_photo("/static/dietitian-photos/a.jpg")
    profile.add_photo("/static/dietitian-photos/b.jpg")

    profile.remove_photo(0)

    assert profile.photos == ("/static/dietitian-photos/b.jpg",)


def test_remove_photo_rejects_an_out_of_range_index() -> None:
    profile = _create()
    profile.add_photo("/static/dietitian-photos/a.jpg")

    with pytest.raises(InvalidDietitianProfileError):
        profile.remove_photo(1)

    with pytest.raises(InvalidDietitianProfileError):
        profile.remove_photo(-1)


def test_create_leaves_first_and_last_name_unset_by_default() -> None:
    profile = _create()

    assert profile.first_name is None
    assert profile.last_name is None


def test_create_accepts_an_optional_first_and_last_name() -> None:
    profile = _create(first_name="Jan", last_name="Kowalski")

    assert profile.first_name == "Jan"
    assert profile.last_name == "Kowalski"


def test_create_rejects_a_first_name_with_special_characters() -> None:
    with pytest.raises(InvalidDietitianProfileError):
        _create(first_name="Jan; DROP TABLE users;")


def test_create_rejects_a_last_name_with_special_characters() -> None:
    with pytest.raises(InvalidDietitianProfileError):
        _create(last_name="Kowalski<script>")


def test_update_details_sets_first_and_last_name() -> None:
    profile = _create()

    profile.update_details(first_name="Jan", last_name="Kowalski")

    assert profile.first_name == "Jan"
    assert profile.last_name == "Kowalski"


def test_update_details_leaves_names_unchanged_when_not_given() -> None:
    profile = _create(first_name="Jan", last_name="Kowalski")

    profile.update_details(description="Updated description.")

    assert profile.first_name == "Jan"
    assert profile.last_name == "Kowalski"


def test_update_details_rejects_an_invalid_first_name() -> None:
    profile = _create()

    with pytest.raises(InvalidDietitianProfileError):
        profile.update_details(first_name="Jan  Kowalski")
