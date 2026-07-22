from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RenameConversationCommand:
    conversation_id: UUID
    user_id: UUID
    title: str
