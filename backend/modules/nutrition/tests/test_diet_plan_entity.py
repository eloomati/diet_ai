from uuid import uuid4

import pytest

from backend.modules.nutrition.domain import (
    DietDay,
    DietGoal,
    DietPlan,
    DietType,
    InvalidDietPlanError,
    Meal,
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
