from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.identity.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class UserSummaryResult:
    id: UUID
    email: str
    status: str
    role: str
    email_verified: bool
    created_at: datetime

    @classmethod
    def from_domain(cls, user: User) -> "UserSummaryResult":
        return cls(
            id=user.id,
            email=user.email.value,
            status=user.status.value,
            role=user.role.value,
            email_verified=user.email_verified,
            created_at=user.created_at,
        )
