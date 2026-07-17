from pydantic import BaseModel, Field

from backend.modules.nutrition.application.dto.nutrition_profile_dto import NutritionProfileResult
from backend.modules.nutrition.domain import ActivityLevel, DietGoal, DietType


class CreateNutritionProfileRequest(BaseModel):
    age: int = Field(ge=1, le=120)
    height_cm: int = Field(ge=50, le=250)
    weight_kg: float = Field(ge=20, le=400)
    activity_level: ActivityLevel
    goal: DietGoal
    diet_type: DietType


class UpdateNutritionProfileRequest(BaseModel):
    age: int | None = Field(default=None, ge=1, le=120)
    height_cm: int | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=20, le=400)
    activity_level: ActivityLevel | None = None
    goal: DietGoal | None = None
    diet_type: DietType | None = None


class NutritionProfileResponse(BaseModel):
    profile_id: str
    user_id: str
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str
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
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
