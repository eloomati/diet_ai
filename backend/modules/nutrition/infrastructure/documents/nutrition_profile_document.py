from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field
from pymongo import ASCENDING, IndexModel


class WeeklyObligationEmbed(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    label: str


class NutritionProfileDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str
    weekly_obligations: list[WeeklyObligationEmbed] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "nutrition_profiles"
        # Unique index: DB-level backstop for "one profile per user", alongside
        # the application-layer check in CreateNutritionProfileUseCase.
        indexes = [
            IndexModel(
                [("user_id", ASCENDING)],
                name="ix_nutrition_profiles_user_id",
                unique=True,
            ),
        ]
