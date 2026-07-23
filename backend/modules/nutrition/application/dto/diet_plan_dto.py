from dataclasses import dataclass
from datetime import date, time
from uuid import UUID

from backend.modules.nutrition.domain.entities.diet_plan import DietPlan
from backend.modules.nutrition.domain.value_objects.diet_day import DietDay
from backend.modules.nutrition.domain.value_objects.meal import Meal


@dataclass(frozen=True, slots=True)
class GenerateDietPlanCommand:
    user_id: UUID
    duration_days: int
    requirements: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class ListDietPlansQuery:
    user_id: UUID
    start_date: date | None = None
    end_date: date | None = None


@dataclass(frozen=True, slots=True)
class GetDietPlanQuery:
    user_id: UUID
    plan_id: UUID


@dataclass(frozen=True, slots=True)
class RescheduleMealCommand:
    user_id: UUID
    plan_id: UUID
    day_number: int
    meal_index: int
    new_time: time
    new_day_number: int | None = None


@dataclass(frozen=True, slots=True)
class RenameDietPlanCommand:
    user_id: UUID
    plan_id: UUID
    name: str | None


@dataclass(frozen=True, slots=True)
class MealResult:
    name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    time: str | None

    @classmethod
    def from_domain(cls, meal: Meal) -> "MealResult":
        return cls(
            name=meal.name,
            calories=meal.calories,
            protein=meal.protein,
            carbohydrates=meal.carbohydrates,
            fat=meal.fat,
            time=meal.time.isoformat(timespec="minutes") if meal.time else None,
        )


@dataclass(frozen=True, slots=True)
class DietDayResult:
    day_number: int
    meals: tuple[MealResult, ...]

    @classmethod
    def from_domain(cls, day: DietDay) -> "DietDayResult":
        return cls(
            day_number=day.day_number,
            meals=tuple(MealResult.from_domain(meal) for meal in day.meals),
        )


@dataclass(frozen=True, slots=True)
class DietPlanResult:
    plan_id: str
    user_id: str
    goal: str
    diet_type: str
    duration_days: int
    requirements: tuple[str, ...]
    days: tuple[DietDayResult, ...]
    created_at: str
    updated_at: str
    name: str | None = None

    @classmethod
    def from_domain(cls, plan: DietPlan) -> "DietPlanResult":
        return cls(
            plan_id=str(plan.id),
            user_id=str(plan.user_id),
            goal=plan.goal.value,
            diet_type=plan.diet_type.value,
            duration_days=plan.duration_days,
            requirements=plan.requirements,
            days=tuple(DietDayResult.from_domain(day) for day in plan.days),
            name=plan.name,
            created_at=plan.created_at.isoformat(),
            updated_at=plan.updated_at.isoformat(),
        )


@dataclass(frozen=True, slots=True)
class DietPlanSummaryResult:
    plan_id: str
    goal: str
    diet_type: str
    duration_days: int
    created_at: str
    name: str | None = None

    @classmethod
    def from_domain(cls, plan: DietPlan) -> "DietPlanSummaryResult":
        return cls(
            plan_id=str(plan.id),
            goal=plan.goal.value,
            diet_type=plan.diet_type.value,
            duration_days=plan.duration_days,
            name=plan.name,
            created_at=plan.created_at.isoformat(),
        )
