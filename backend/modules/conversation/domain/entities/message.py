from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.conversation.domain.value_objects.message_role import MessageRole


@dataclass(frozen=True, slots=True)
class Message:
    id: UUID
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    token_usage: int | None = None

    @classmethod
    def create(cls, role: MessageRole, content: str, token_usage: int | None = None) -> "Message":
        return cls(id=uuid4(), role=role, content=content, token_usage=token_usage)
