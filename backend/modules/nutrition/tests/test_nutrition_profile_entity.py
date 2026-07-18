from datetime import time
from uuid import uuid4

import pytest

from backend.modules.nutrition.domain import (
    ActivityLevel,
    DayOfWeek,
    DietGoal,
    DietType,
    InvalidNutritionProfileError,
    NutritionProfile,
    WeeklyObligation,
)


def _create(**overrides) -> NutritionProfile:
    defaults = dict(
        user_id=uuid4(),
        age=29,
        height_cm=187,
        weight_kg=80,
        activity_level=ActivityLevel.HIGH,
        goal=DietGoal.MUSCLE_GAIN,
        diet_type=DietType.VEGETARIAN,
    )
    defaults.update(overrides)
    return NutritionProfile.create(**defaults)


def test_create_sets_fields() -> None:
    profile = _create()

    assert profile.age == 29
    assert profile.height_cm == 187
    assert profile.weight_kg == 80
    assert profile.activity_level == ActivityLevel.HIGH
    assert profile.goal == DietGoal.MUSCLE_GAIN
    assert profile.diet_type == DietType.VEGETARIAN


@pytest.mark.parametrize(
    "overrides",
    [
        {"age": 0},
        {"age": 121},
        {"height_cm": 49},
        {"height_cm": 251},
        {"weight_kg": 19},
        {"weight_kg": 401},
    ],
)
def test_create_rejects_out_of_range_values(overrides) -> None:
    with pytest.raises(InvalidNutritionProfileError):
        _create(**overrides)


def test_update_changes_only_provided_fields() -> None:
    profile = _create()

    profile.update(weight_kg=82, activity_level=ActivityLevel.VERY_HIGH)

    assert profile.weight_kg == 82
    assert profile.activity_level == ActivityLevel.VERY_HIGH
    # Untouched fields stay as they were.
    assert profile.age == 29
    assert profile.height_cm == 187
    assert profile.goal == DietGoal.MUSCLE_GAIN
    assert profile.diet_type == DietType.VEGETARIAN


def test_update_rejects_out_of_range_values() -> None:
    profile = _create()

    with pytest.raises(InvalidNutritionProfileError):
        profile.update(age=200)

    # Rejected update must not have partially applied.
    assert profile.age == 29


def test_as_prompt_text_includes_key_fields() -> None:
    profile = _create()

    text = profile.as_prompt_text()

    assert "29" in text
    assert "187cm" in text
    assert "80kg" in text
    assert "HIGH" in text
    assert "MUSCLE_GAIN" in text
    assert "VEGETARIAN" in text


def test_as_prompt_text_omits_commitments_clause_when_no_obligations() -> None:
    profile = _create()

    assert "commitments" not in profile.as_prompt_text()


def test_as_prompt_text_includes_weekly_obligations() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.WED, start_time=time(18, 0), end_time=time(19, 0), label="Training"
    )
    profile = _create(weekly_obligations=(obligation,))

    text = profile.as_prompt_text()

    assert "WED" in text
    assert "18:00-19:00" in text
    assert "Training" in text


def test_create_defaults_to_no_obligations() -> None:
    profile = _create()

    assert profile.weekly_obligations == ()


def test_update_sets_weekly_obligations() -> None:
    profile = _create()
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )

    profile.update(weekly_obligations=(obligation,))

    assert profile.weekly_obligations == (obligation,)


def test_update_without_obligations_keeps_existing_ones() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )
    profile = _create(weekly_obligations=(obligation,))

    profile.update(weight_kg=82)

    assert profile.weekly_obligations == (obligation,)


def test_update_can_clear_obligations_with_empty_tuple() -> None:
    obligation = WeeklyObligation(
        day_of_week=DayOfWeek.MON, start_time=time(9, 0), end_time=time(17, 0), label="Work"
    )
    profile = _create(weekly_obligations=(obligation,))

    profile.update(weekly_obligations=())

    assert profile.weekly_obligations == ()
