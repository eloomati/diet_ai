from datetime import UTC, datetime
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
    # Defaulted (unlike created_at): plans generated before Phase 9 Stage 3
    # predate this field and have no value to backfill from.
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "diet_plans"
        # Not unique: unlike NutritionProfile, a user can have many diet plans.
        # Compound (not just user_id): Stage 5 added date-range filtering on
        # created_at, always alongside a user_id match — a plain user_id index
        # still covers unfiltered list_by_user_id (Mongo can use a compound
        # index's leading prefix), but the range clause benefits from
        # created_at being indexed too.
        indexes = [
            IndexModel(
                [("user_id", ASCENDING), ("created_at", ASCENDING)],
                name="ix_diet_plans_user_id_created_at",
            ),
        ]
