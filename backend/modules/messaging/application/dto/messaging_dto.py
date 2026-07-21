from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender


@dataclass(frozen=True, slots=True)
class SendMessageCommand:
    thread_id: UUID
    caller_id: UUID
    content: str
    diet_plan_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class DietitianThreadResult:
    id: UUID
    user_id: UUID
    dietitian_id: UUID
    created_at: datetime
    # Resolved relative to whichever caller asked — "the other side of my
    # conversation" — not a fixed field on the entity itself.
    other_participant_email: str | None = None

    @classmethod
    def from_domain(
        cls, thread: DietitianThread, other_participant_email: str | None = None
    ) -> "DietitianThreadResult":
        return cls(
            id=thread.id,
            user_id=thread.user_id,
            dietitian_id=thread.dietitian_id,
            created_at=thread.created_at,
            other_participant_email=other_participant_email,
        )


@dataclass(frozen=True, slots=True)
class DietitianMessageResult:
    id: UUID
    thread_id: UUID
    sender: MessageSender
    content: str
    diet_plan_id: UUID | None
    created_at: datetime

    @classmethod
    def from_domain(cls, message: DietitianMessage) -> "DietitianMessageResult":
        return cls(
            id=message.id,
            thread_id=message.thread_id,
            sender=message.sender,
            content=message.content,
            diet_plan_id=message.diet_plan_id,
            created_at=message.created_at,
        )
