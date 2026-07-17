from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.conversation.api.dependencies import (
    get_conversation_history_use_case,
    get_create_conversation_use_case,
    get_list_conversations_use_case,
    get_send_message_use_case,
)
from backend.modules.conversation.api.schemas import (
    ConversationHistoryResponse,
    ConversationSummaryResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    MessageResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from backend.modules.conversation.application import (
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    GetConversationHistoryQuery,
    GetConversationHistoryUseCase,
    ListConversationsQuery,
    ListConversationsUseCase,
    SendMessageCommand,
    SendMessageUseCase,
)
from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/conversations", tags=["conversation"])


@router.post("", response_model=CreateConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateConversationUseCase = Depends(get_create_conversation_use_case),
) -> CreateConversationResponse:
    result = await use_case.execute(
        CreateConversationCommand(
            user_id=current_user.id,
            title=request.title,
            category=request.category.value,
        )
    )
    return CreateConversationResponse(
        conversation_id=result.conversation_id,
        title=result.title,
        category=result.category,
        status=result.status,
    )


@router.get("", response_model=list[ConversationSummaryResponse], status_code=status.HTTP_200_OK)
async def list_conversations(
    current_user: User = Depends(get_current_user),
    use_case: ListConversationsUseCase = Depends(get_list_conversations_use_case),
) -> list[ConversationSummaryResponse]:
    summaries = await use_case.execute(ListConversationsQuery(user_id=current_user.id))
    return [
        ConversationSummaryResponse(
            conversation_id=summary.conversation_id,
            title=summary.title,
            category=summary.category,
            status=summary.status,
            updated_at=summary.updated_at,
        )
        for summary in summaries
    ]


@router.get(
    "/{conversation_id}", response_model=ConversationHistoryResponse, status_code=status.HTTP_200_OK
)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetConversationHistoryUseCase = Depends(get_conversation_history_use_case),
) -> ConversationHistoryResponse:
    try:
        result = await use_case.execute(
            GetConversationHistoryQuery(conversation_id=conversation_id, user_id=current_user.id)
        )
    except ConversationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="Conversation not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return ConversationHistoryResponse(
        conversation_id=result.conversation_id,
        title=result.title,
        category=result.category,
        status=result.status,
        messages=[
            MessageResponse(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
            )
            for message in result.messages
        ],
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: UUID,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    use_case: SendMessageUseCase = Depends(get_send_message_use_case),
) -> SendMessageResponse:
    try:
        result = await use_case.execute(
            SendMessageCommand(
                conversation_id=conversation_id,
                user_id=current_user.id,
                content=request.content,
            )
        )
    except ConversationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="Conversation not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return SendMessageResponse(
        conversation_id=result.conversation_id,
        user_message_id=result.user_message_id,
        assistant_message_id=result.assistant_message_id,
        assistant_content=result.assistant_content,
    )
