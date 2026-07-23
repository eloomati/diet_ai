from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication


@dataclass(frozen=True, slots=True)
class SubmitDietitianApplicationCommand:
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str


@dataclass(frozen=True, slots=True)
class DietitianApplicationResult:
    id: UUID
    user_id: UUID
    experience: str
    diplomas: tuple[str, ...]
    description: str
    status: str
    created_at: datetime

    @classmethod
    def from_domain(cls, application: DietitianApplication) -> "DietitianApplicationResult":
        return cls(
            id=application.id,
            user_id=application.user_id,
            experience=application.experience,
            diplomas=application.diplomas,
            description=application.description,
            status=application.status.value,
            created_at=application.created_at,
        )
