from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.conversation.domain.entities.message import Message
from backend.modules.conversation.domain.events.conversation_events import (
    ConversationCreated,
    MessageAdded,
)
from backend.modules.conversation.domain.exceptions.conversation_domain_errors import (
    ArchivedConversationError,
    InvalidConversationError,
)
from backend.modules.conversation.domain.value_objects.conversation_category import (
    ConversationCategory,
)
from backend.modules.conversation.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from backend.modules.conversation.domain.value_objects.message_role import MessageRole


@dataclass(slots=True)
class Conversation:
    id: UUID
    user_id: UUID
    title: str
    categories: tuple[ConversationCategory, ...]
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    domain_events: list[object] = field(default_factory=list)

    @classmethod
    def create(
        cls, user_id: UUID, title: str, categories: Sequence[ConversationCategory]
    ) -> "Conversation":
        deduped = tuple(dict.fromkeys(categories))
        if not deduped:
            raise InvalidConversationError("A conversation needs at least one category.")

        now = datetime.now(UTC)
        conversation = cls(
            id=uuid4(),
            user_id=user_id,
            title=title,
            categories=deduped,
            created_at=now,
            updated_at=now,
        )
        conversation.domain_events.append(
            ConversationCreated(conversation_id=conversation.id, user_id=user_id)
        )
        return conversation

    def can_receive_messages(self) -> bool:
        return self.status == ConversationStatus.ACTIVE

    def assert_can_receive_messages(self) -> None:
        if not self.can_receive_messages():
            raise ArchivedConversationError("Archived conversations cannot receive new messages.")

    def add_message(self, role: MessageRole, content: str, token_usage: int | None = None) -> Message:
        self.assert_can_receive_messages()
        message = Message.create(role=role, content=content, token_usage=token_usage)
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)
        self.domain_events.append(MessageAdded(conversation_id=self.id, message_id=message.id))
        return message

    def archive(self) -> None:
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.now(UTC)
