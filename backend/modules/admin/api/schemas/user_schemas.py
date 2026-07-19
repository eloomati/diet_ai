from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.admin.application.dto.admin_dto import UserSummaryResult


class UserSummaryResponse(BaseModel):
    id: UUID
    email: str
    status: str
    role: str
    email_verified: bool
    created_at: datetime

    @classmethod
    def from_result(cls, result: UserSummaryResult) -> "UserSummaryResponse":
        return cls(
            id=result.id,
            email=result.email,
            status=result.status,
            role=result.role,
            email_verified=result.email_verified,
            created_at=result.created_at,
        )
