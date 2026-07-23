from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.messaging.domain.exceptions.messaging_domain_errors import (
    InvalidMessageError,
)
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender


@dataclass(slots=True)
class DietitianMessage:
    id: UUID
    thread_id: UUID
    sender: MessageSender
    content: str
    diet_plan_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        thread_id: UUID,
        sender: MessageSender,
        content: str,
        diet_plan_id: UUID | None = None,
    ) -> "DietitianMessage":
        if not content.strip():
            raise InvalidMessageError("Message content cannot be empty.")
        return cls(
            id=uuid4(),
            thread_id=thread_id,
            sender=sender,
            content=content,
            diet_plan_id=diet_plan_id,
        )
