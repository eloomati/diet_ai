from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SendMessageCommand:
    conversation_id: UUID
    user_id: UUID
    content: str


@dataclass(frozen=True, slots=True)
class SendMessageResult:
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    assistant_content: str
