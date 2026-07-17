from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateConversationCommand:
    user_id: UUID
    title: str
    category: str


@dataclass(frozen=True, slots=True)
class CreateConversationResult:
    conversation_id: str
    title: str
    category: str
    status: str
