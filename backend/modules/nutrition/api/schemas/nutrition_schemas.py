from datetime import time

from pydantic import BaseModel, Field

from backend.modules.nutrition.application.dto.nutrition_profile_dto import (
    NutritionProfileResult,
    WeeklyObligationResult,
)
from backend.modules.nutrition.domain import ActivityLevel, DayOfWeek, DietGoal, DietType


class WeeklyObligationRequest(BaseModel):
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    label: str = Field(min_length=1, max_length=100)


class CreateNutritionProfileRequest(BaseModel):
    age: int = Field(ge=1, le=120)
    height_cm: int = Field(ge=50, le=250)
    weight_kg: float = Field(ge=20, le=400)
    activity_level: ActivityLevel
    goal: DietGoal
    diet_type: DietType
    weekly_obligations: list[WeeklyObligationRequest] = Field(default_factory=list)


class UpdateNutritionProfileRequest(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    height_cm: int | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=400)
    activity_level: ActivityLevel | None = None
    goal: DietGoal | None = None
    diet_type: DietType | None = None
    weekly_obligations: list[WeeklyObligationRequest] | None = None


class WeeklyObligationResponse(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    label: str

    @classmethod
    def from_result(cls, result: WeeklyObligationResult) -> "WeeklyObligationResponse":
        return cls(
            day_of_week=result.day_of_week,
            start_time=result.start_time,
            end_time=result.end_time,
            label=result.label,
        )


class NutritionProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str
    weekly_obligations: list[WeeklyObligationResponse]
    created_at: str
    updated_at: str

    @classmethod
    def from_result(cls, result: NutritionProfileResult) -> "NutritionProfileResponse":
        return cls(
            profile_id=result.profile_id,
            user_id=result.user_id,
            age=result.age,
            height_cm=result.height_cm,
            weight_kg=result.weight_kg,
            activity_level=result.activity_level,
            goal=result.goal,
            diet_type=result.diet_type,
            weekly_obligations=[
                WeeklyObligationResponse.from_result(o) for o in result.weekly_obligations
            ],
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
