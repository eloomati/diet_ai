from backend.modules.conversation.domain.entities.conversation import Conversation
from backend.modules.conversation.domain.entities.message import Message
from backend.modules.conversation.domain.value_objects.conversation_category import (
    ConversationCategory,
)
from backend.modules.conversation.domain.value_objects.conversation_status import (
    ConversationStatus,
)
from backend.modules.conversation.domain.value_objects.message_role import MessageRole
from backend.modules.conversation.infrastructure.documents.conversation_document import (
    ConversationDocument,
    MessageEmbedded,
)


class ConversationMapper:
    @staticmethod
    def to_domain(document: ConversationDocument) -> Conversation:
        return Conversation(
            id=document.id,
            user_id=document.user_id,
            title=document.title,
            categories=tuple(ConversationCategory(c) for c in document.categories),
            status=ConversationStatus(document.status),
            messages=[
                Message(
                    id=message.id,
                    role=MessageRole(message.role),
                    content=message.content,
                    created_at=message.created_at,
                    token_usage=message.token_usage,
                )
                for message in document.messages
            ],
            created_at=document.created_at,
            updated_at=document.updated_at,
            domain_events=[],
        )

    @staticmethod
    def to_document(conversation: Conversation) -> ConversationDocument:
        return ConversationDocument(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            categories=[c.value for c in conversation.categories],
            status=conversation.status.value,
            messages=[
                MessageEmbedded(
                    id=message.id,
                    role=message.role.value,
                    content=message.content,
                    created_at=message.created_at,
                    token_usage=message.token_usage,
                )
                for message in conversation.messages
            ],
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
