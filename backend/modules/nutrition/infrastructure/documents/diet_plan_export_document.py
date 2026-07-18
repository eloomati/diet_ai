from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field
from pymongo import ASCENDING, IndexModel


class DietPlanExportDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    diet_plan_id: UUID
    filename: str
    created_at: datetime

    class Settings:
        name = "diet_plan_exports"
        # Not unique: a plan can be exported more than once.
        indexes = [
            IndexModel([("diet_plan_id", ASCENDING)], name="ix_diet_plan_exports_diet_plan_id"),
        ]
