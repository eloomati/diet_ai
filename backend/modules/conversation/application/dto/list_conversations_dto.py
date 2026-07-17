from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ListConversationsQuery:
    user_id: UUID


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    conversation_id: str
    title: str
    category: str
    status: str
    updated_at: str
