from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import Field


class CombinedDietPlanExportDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    diet_plan_ids: list[UUID]
    filename: str
    created_at: datetime

    class Settings:
        name = "combined_diet_plan_exports"
