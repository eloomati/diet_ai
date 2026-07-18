from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel


class MealEmbed(BaseModel):
    name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    # str, not a native time type: MongoDB/BSON has no standalone "time-of-day"
    # type (only full datetimes), so this stores "HH:MM" strings instead.
    time: str | None = None


class DietDayEmbed(BaseModel):
    day_number: int
    meals: list[MealEmbed]


class DietPlanDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    goal: str
    diet_type: str
    duration_days: int
    requirements: list[str]
    days: list[DietDayEmbed]
    created_at: datetime

    class Settings:
        name = "diet_plans"
        # Not unique: unlike NutritionProfile, a user can have many diet plans.
        indexes = [
            IndexModel([("user_id", ASCENDING)], name="ix_diet_plans_user_id"),
        ]
