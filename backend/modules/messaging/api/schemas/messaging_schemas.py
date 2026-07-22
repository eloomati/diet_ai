from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.messaging.application.dto.messaging_dto import (
    DietitianMessageResult,
    DietitianThreadResult,
)
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender


class SendMessageRequest(BaseModel):
    content: str
    diet_plan_id: UUID | None = None


class DietitianThreadResponse(BaseModel):
    id: UUID
    user_id: UUID
    dietitian_id: UUID
    created_at: datetime
    other_participant_email: str | None

    @classmethod
    def from_result(cls, result: DietitianThreadResult) -> "DietitianThreadResponse":
        return cls(
            id=result.id,
            user_id=result.user_id,
            dietitian_id=result.dietitian_id,
            created_at=result.created_at,
            other_participant_email=result.other_participant_email,
        )


class DietitianMessageResponse(BaseModel):
    id: UUID
    thread_id: UUID
    sender: MessageSender
    content: str
    diet_plan_id: UUID | None
    created_at: datetime

    @classmethod
    def from_result(cls, result: DietitianMessageResult) -> "DietitianMessageResponse":
        return cls(
            id=result.id,
            thread_id=result.thread_id,
            sender=result.sender,
            content=result.content,
            diet_plan_id=result.diet_plan_id,
            created_at=result.created_at,
        )
