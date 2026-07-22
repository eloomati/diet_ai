from datetime import time

from pydantic import BaseModel, Field

from backend.modules.nutrition.application.dto.diet_plan_dto import (
    DietDayResult,
    DietPlanResult,
    DietPlanSummaryResult,
    MealResult,
)


class GenerateDietPlanRequest(BaseModel):
    duration_days: int = Field(ge=1, le=14)
    requirements: list[str] | None = None


class RescheduleMealRequest(BaseModel):
    day_number: int = Field(ge=1)
    meal_name: str = Field(min_length=1)
    new_time: time


class RenameDietPlanRequest(BaseModel):
    # Explicit `null` clears it back to the default goal/diet_type/duration
    # display — same convention as `UpdateMeRequest.display_name`.
    name: str | None = Field(default=None, min_length=1, max_length=200)


class MealResponse(BaseModel):
    name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    time: str | None

    @classmethod
    def from_result(cls, result: MealResult) -> "MealResponse":
        return cls(
            name=result.name,
            calories=result.calories,
            protein=result.protein,
            carbohydrates=result.carbohydrates,
            fat=result.fat,
            time=result.time,
        )


class DietDayResponse(BaseModel):
    day_number: int
    meals: list[MealResponse]

    @classmethod
    def from_result(cls, result: DietDayResult) -> "DietDayResponse":
        return cls(
            day_number=result.day_number,
            meals=[MealResponse.from_result(meal) for meal in result.meals],
        )


class DietPlanResponse(BaseModel):
    plan_id: str
    user_id: str
    goal: str
    diet_type: str
    duration_days: int
    requirements: list[str]
    days: list[DietDayResponse]
    name: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_result(cls, result: DietPlanResult) -> "DietPlanResponse":
        return cls(
            plan_id=result.plan_id,
            user_id=result.user_id,
            goal=result.goal,
            diet_type=result.diet_type,
            duration_days=result.duration_days,
            requirements=list(result.requirements),
            days=[DietDayResponse.from_result(day) for day in result.days],
            name=result.name,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class DietPlanSummaryResponse(BaseModel):
    plan_id: str
    goal: str
    diet_type: str
    duration_days: int
    name: str | None
    created_at: str

    @classmethod
    def from_result(cls, result: DietPlanSummaryResult) -> "DietPlanSummaryResponse":
        return cls(
            plan_id=result.plan_id,
            goal=result.goal,
            diet_type=result.diet_type,
            duration_days=result.duration_days,
            name=result.name,
            created_at=result.created_at,
        )
