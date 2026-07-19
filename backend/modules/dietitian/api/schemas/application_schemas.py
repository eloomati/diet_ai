from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    DietitianApplicationResult,
)


class SubmitDietitianApplicationRequest(BaseModel):
    experience: str = Field(min_length=1)
    diplomas: list[str] = Field(default_factory=list)
    description: str = Field(min_length=1)


class DietitianApplicationResponse(BaseModel):
    id: UUID
    user_id: UUID
    experience: str
    diplomas: list[str]
    description: str
    status: str
    created_at: datetime

    @classmethod
    def from_result(cls, result: DietitianApplicationResult) -> "DietitianApplicationResponse":
        return cls(
            id=result.id,
            user_id=result.user_id,
            experience=result.experience,
            diplomas=list(result.diplomas),
            description=result.description,
            status=result.status,
            created_at=result.created_at,
        )
