from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, time
from uuid import UUID, uuid4

from backend.modules.nutrition.domain.exceptions.diet_plan_domain_errors import (
    InvalidDietPlanError,
    MealNotFoundError,
)
from backend.modules.nutrition.domain.value_objects.diet_day import DietDay
from backend.modules.nutrition.domain.value_objects.diet_goal import DietGoal
from backend.modules.nutrition.domain.value_objects.diet_type import DietType

_MIN_DURATION_DAYS, _MAX_DURATION_DAYS = 1, 14


@dataclass(slots=True)
class DietPlan:
    id: UUID
    user_id: UUID
    goal: DietGoal
    diet_type: DietType
    duration_days: int
    requirements: tuple[str, ...]
    days: tuple[DietDay, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UUID,
        goal: DietGoal,
        diet_type: DietType,
        duration_days: int,
        days: tuple[DietDay, ...],
        requirements: tuple[str, ...] = (),
    ) -> "DietPlan":
        cls._validate(duration_days, days)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            goal=goal,
            diet_type=diet_type,
            duration_days=duration_days,
            requirements=requirements,
            days=days,
            created_at=now,
            updated_at=now,
        )

    def reschedule_meal(self, day_number: int, meal_name: str, new_time: time) -> None:
        day_index = next(
            (i for i, day in enumerate(self.days) if day.day_number == day_number), None
        )
        if day_index is None:
            raise MealNotFoundError(f"Day {day_number} not found in this plan.")

        day = self.days[day_index]
        meal_index = next(
            (i for i, meal in enumerate(day.meals) if meal.name == meal_name), None
        )
        if meal_index is None:
            raise MealNotFoundError(f"Meal '{meal_name}' not found on day {day_number}.")

        new_meals = list(day.meals)
        new_meals[meal_index] = replace(new_meals[meal_index], time=new_time)
        new_day = replace(day, meals=tuple(new_meals))

        new_days = list(self.days)
        new_days[day_index] = new_day
        self.days = tuple(new_days)
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate(duration_days: int, days: tuple[DietDay, ...]) -> None:
        if not (_MIN_DURATION_DAYS <= duration_days <= _MAX_DURATION_DAYS):
            raise InvalidDietPlanError(
                f"Duration must be between {_MIN_DURATION_DAYS} and {_MAX_DURATION_DAYS} days."
            )
        if len(days) != duration_days:
            raise InvalidDietPlanError(
                f"Expected {duration_days} days in the plan, got {len(days)}."
            )
        for meal_day in days:
            for meal in meal_day.meals:
                if meal.calories < 0 or meal.protein < 0 or meal.carbohydrates < 0 or meal.fat < 0:
                    raise InvalidDietPlanError(f"Meal '{meal.name}' has a negative macro value.")
