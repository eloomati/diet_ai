from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile


@dataclass(frozen=True, slots=True)
class UpdateDietitianProfileCommand:
    user_id: UUID
    experience: str | None = None
    diplomas: tuple[str, ...] | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class DietitianProfileResult:
    id: UUID
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str
    photos: tuple[str, ...]
    created_at: datetime

    @classmethod
    def from_domain(cls, profile: DietitianProfile) -> "DietitianProfileResult":
        return cls(
            id=profile.id,
            user_id=profile.user_id,
            experience=profile.experience,
            diplomas=profile.diplomas,
            description=profile.description,
            photos=profile.photos,
            created_at=profile.created_at,
        )
