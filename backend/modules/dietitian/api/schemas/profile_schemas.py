from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.dietitian.application.dto.dietitian_profile_dto import DietitianProfileResult


class DietitianProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    experience: str
    diplomas: list[str]
    description: str
    photos: list[str]
    created_at: datetime

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
        )
