from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreateConversationCommand:
    user_id: UUID
    title: str
    categories: list[str]


@dataclass(frozen=True, slots=True)
class CreateConversationResult:
    conversation_id: str
    title: str
    categories: list[str]
    status: str
