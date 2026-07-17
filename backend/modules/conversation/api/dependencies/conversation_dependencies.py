from fastapi import Depends

from backend.modules.ai.domain import LLMProvider
from backend.modules.ai.infrastructure.provider_factory import build_llm_provider
from backend.modules.conversation.application import (
    CreateConversationUseCase,
    GetConversationHistoryUseCase,
    ListConversationsUseCase,
    SendMessageUseCase,
)
from backend.modules.conversation.domain import ConversationRepository
from backend.modules.conversation.infrastructure.repository.mongo_conversation_repository import (
    MongoConversationRepository,
)
from backend.shared.config import get_settings


def get_conversation_repository() -> ConversationRepository:
    return MongoConversationRepository()


def get_llm_provider() -> LLMProvider:
    return build_llm_provider(get_settings())


def get_create_conversation_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> CreateConversationUseCase:
    return CreateConversationUseCase(repository)


def get_list_conversations_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ListConversationsUseCase:
    return ListConversationsUseCase(repository)


def get_conversation_history_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> GetConversationHistoryUseCase:
    return GetConversationHistoryUseCase(repository)


def get_send_message_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> SendMessageUseCase:
    return SendMessageUseCase(repository, llm_provider)
