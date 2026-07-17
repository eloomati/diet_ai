from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetConversationHistoryQuery:
    conversation_id: UUID
    user_id: UUID


@dataclass(frozen=True, slots=True)
class MessageView:
    id: str
    role: str
    content: str
    created_at: str


@dataclass(frozen=True, slots=True)
class GetConversationHistoryResult:
    conversation_id: str
    title: str
    category: str
    status: str
    messages: list[MessageView]
