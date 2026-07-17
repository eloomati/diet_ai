from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.nutrition.domain.exceptions.diet_plan_domain_errors import InvalidDietPlanError
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
        return cls(
            id=uuid4(),
            user_id=user_id,
            goal=goal,
            diet_type=diet_type,
            duration_days=duration_days,
            requirements=requirements,
            days=days,
            created_at=datetime.now(UTC),
        )

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
