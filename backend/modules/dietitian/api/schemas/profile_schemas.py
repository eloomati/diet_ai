from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.dietitian.application.dto.dietitian_profile_dto import DietitianProfileResult


class UpdateDietitianProfileRequest(BaseModel):
    experience: str | None = None
    diplomas: list[str] | None = None
    description: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class DietitianProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    experience: str
    diplomas: list[str]
    description: str
    photos: list[str]
    created_at: datetime
    first_name: str | None = None
    last_name: str | None = None

    @classmethod
    def from_result(cls, result: DietitianProfileResult) -> "DietitianProfileResponse":
        return cls(
            id=result.id,
            user_id=result.user_id,
            experience=result.experience,
            diplomas=list(result.diplomas),
            description=result.description,
            photos=list(result.photos),
            created_at=result.created_at,
            first_name=result.first_name,
            last_name=result.last_name,
        )
