from datetime import time
from uuid import uuid4

import pytest

from backend.modules.nutrition.domain import (
    DietDay,
    DietGoal,
    DietPlan,
    DietType,
    InvalidDietPlanError,
    Meal,
    MealNotFoundError,
)


def _meal(**overrides) -> Meal:
    defaults = dict(name="Oatmeal", calories=400, protein=20, carbohydrates=60, fat=10)
    defaults.update(overrides)
    return Meal(**defaults)


def _days(count: int, **meal_overrides) -> tuple[DietDay, ...]:
    return tuple(DietDay(day_number=i + 1, meals=(_meal(**meal_overrides),)) for i in range(count))


def _create(**overrides) -> DietPlan:
    defaults = dict(
        user_id=uuid4(),
        goal=DietGoal.MUSCLE_GAIN,
        diet_type=DietType.VEGETARIAN,
        duration_days=3,
        days=_days(3),
        requirements=("high protein",),
    )
    defaults.update(overrides)
    return DietPlan.create(**defaults)


def test_create_sets_fields() -> None:
    plan = _create()

    assert plan.goal == DietGoal.MUSCLE_GAIN
    assert plan.diet_type == DietType.VEGETARIAN
    assert plan.duration_days == 3
    assert len(plan.days) == 3
    assert plan.requirements == ("high protein",)


def test_create_rejects_duration_out_of_range() -> None:
    with pytest.raises(InvalidDietPlanError):
        _create(duration_days=0, days=_days(0))

    with pytest.raises(InvalidDietPlanError):
        _create(duration_days=15, days=_days(15))


def test_create_rejects_day_count_mismatch() -> None:
    with pytest.raises(InvalidDietPlanError):
        _create(duration_days=3, days=_days(2))


@pytest.mark.parametrize(
    "meal_overrides",
    [{"calories": -1}, {"protein": -1}, {"carbohydrates": -1}, {"fat": -1}],
)
def test_create_rejects_negative_macros(meal_overrides) -> None:
    with pytest.raises(InvalidDietPlanError):
        _create(duration_days=1, days=_days(1, **meal_overrides))


def test_create_sets_updated_at_equal_to_created_at() -> None:
    plan = _create()

    assert plan.updated_at == plan.created_at


def test_reschedule_meal_updates_only_the_target_meal() -> None:
    plan = _create(duration_days=1, days=(DietDay(day_number=1, meals=(_meal(name="Oatmeal"),)),))

    plan.reschedule_meal(day_number=1, meal_name="Oatmeal", new_time=time(8, 0))

    assert plan.days[0].meals[0].time == time(8, 0)
    assert plan.days[0].meals[0].name == "Oatmeal"
    assert plan.days[0].meals[0].calories == 400


def test_reschedule_meal_leaves_other_meals_and_days_untouched() -> None:
    plan = _create(
        duration_days=2,
        days=(
            DietDay(day_number=1, meals=(_meal(name="Oatmeal"), _meal(name="Lunch"))),
            DietDay(day_number=2, meals=(_meal(name="Oatmeal"),)),
        ),
    )

    plan.reschedule_meal(day_number=1, meal_name="Oatmeal", new_time=time(8, 0))

    assert plan.days[0].meals[0].time == time(8, 0)
    assert plan.days[0].meals[1].time is None
    assert plan.days[1].meals[0].time is None


def test_reschedule_meal_bumps_updated_at() -> None:
    plan = _create(duration_days=1, days=(DietDay(day_number=1, meals=(_meal(),)),))
    original_updated_at = plan.updated_at

    plan.reschedule_meal(day_number=1, meal_name="Oatmeal", new_time=time(8, 0))

    assert plan.updated_at >= original_updated_at


def test_reschedule_meal_with_unknown_day_raises() -> None:
    plan = _create(duration_days=1, days=(DietDay(day_number=1, meals=(_meal(),)),))

    with pytest.raises(MealNotFoundError):
        plan.reschedule_meal(day_number=99, meal_name="Oatmeal", new_time=time(8, 0))


def test_reschedule_meal_with_unknown_meal_name_raises() -> None:
    plan = _create(duration_days=1, days=(DietDay(day_number=1, meals=(_meal(),)),))

    with pytest.raises(MealNotFoundError):
        plan.reschedule_meal(day_number=1, meal_name="Nonexistent", new_time=time(8, 0))
