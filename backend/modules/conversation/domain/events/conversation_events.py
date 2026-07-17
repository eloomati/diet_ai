from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ConversationCreated:
    conversation_id: UUID
    user_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class MessageAdded:
    conversation_id: UUID
    message_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
