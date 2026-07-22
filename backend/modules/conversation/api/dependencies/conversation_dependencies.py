from fastapi import Depends

from backend.modules.ai.domain import LLMProvider
from backend.modules.ai.infrastructure.provider_factory import get_llm_provider
from backend.modules.conversation.application import (
    ArchiveConversationUseCase,
    CreateConversationUseCase,
    DeleteConversationUseCase,
    GetConversationHistoryUseCase,
    ListConversationsUseCase,
    RenameConversationUseCase,
    SendMessageUseCase,
)
from backend.modules.conversation.domain import ConversationRepository
from backend.modules.conversation.infrastructure.repository.mongo_conversation_repository import (
    MongoConversationRepository,
)
from backend.modules.nutrition.domain import NutritionProfileRepository
from backend.modules.nutrition.infrastructure.repository.mongo_nutrition_profile_repository import (
    MongoNutritionProfileRepository,
)


def get_conversation_repository() -> ConversationRepository:
    return MongoConversationRepository()


def get_nutrition_profile_repository() -> NutritionProfileRepository:
    return MongoNutritionProfileRepository()


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
    nutrition_profile_repository: NutritionProfileRepository = Depends(get_nutrition_profile_repository),
) -> SendMessageUseCase:
    return SendMessageUseCase(repository, llm_provider, nutrition_profile_repository)


def get_archive_conversation_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> ArchiveConversationUseCase:
    return ArchiveConversationUseCase(repository)


def get_delete_conversation_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> DeleteConversationUseCase:
    return DeleteConversationUseCase(repository)


def get_rename_conversation_use_case(
    repository: ConversationRepository = Depends(get_conversation_repository),
) -> RenameConversationUseCase:
    return RenameConversationUseCase(repository)
