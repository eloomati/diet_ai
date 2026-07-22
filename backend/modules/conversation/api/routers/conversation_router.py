from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.conversation.api.dependencies import (
    get_archive_conversation_use_case,
    get_conversation_history_use_case,
    get_create_conversation_use_case,
    get_delete_conversation_use_case,
    get_list_conversations_use_case,
    get_rename_conversation_use_case,
    get_send_message_use_case,
)
from backend.modules.conversation.api.schemas import (
    ConversationHistoryResponse,
    ConversationSummaryResponse,
    CreateConversationRequest,
    CreateConversationResponse,
    MessageResponse,
    RenameConversationRequest,
    SendMessageRequest,
    SendMessageResponse,
)
from backend.modules.conversation.application import (
    ArchiveConversationCommand,
    ArchiveConversationUseCase,
    ConversationNotFoundError,
    CreateConversationCommand,
    CreateConversationUseCase,
    DeleteConversationCommand,
    DeleteConversationUseCase,
    GetConversationHistoryQuery,
    GetConversationHistoryUseCase,
    ListConversationsQuery,
    ListConversationsUseCase,
    RenameConversationCommand,
    RenameConversationUseCase,
    SendMessageCommand,
    SendMessageUseCase,
)
from backend.modules.conversation.domain import ArchivedConversationError
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
            categories=[c.value for c in request.categories],
        )
    )
    return CreateConversationResponse(
        conversation_id=result.conversation_id,
        title=result.title,
        categories=result.categories,
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
            categories=summary.categories,
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
        categories=result.categories,
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


@router.patch(
    "/{conversation_id}",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def rename_conversation(
    conversation_id: UUID,
    request: RenameConversationRequest,
    current_user: User = Depends(get_current_user),
    use_case: RenameConversationUseCase = Depends(get_rename_conversation_use_case),
) -> ConversationHistoryResponse:
    try:
        result = await use_case.execute(
            RenameConversationCommand(
                conversation_id=conversation_id, user_id=current_user.id, title=request.title
            )
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
        categories=result.categories,
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
    except ArchivedConversationError as exc:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
        ) from exc

    return SendMessageResponse(
        conversation_id=result.conversation_id,
        user_message_id=result.user_message_id,
        assistant_message_id=result.assistant_message_id,
        assistant_content=result.assistant_content,
    )


@router.post(
    "/{conversation_id}/archive",
    response_model=ConversationHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def archive_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ArchiveConversationUseCase = Depends(get_archive_conversation_use_case),
) -> ConversationHistoryResponse:
    try:
        result = await use_case.execute(
            ArchiveConversationCommand(conversation_id=conversation_id, user_id=current_user.id)
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
        categories=result.categories,
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


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: DeleteConversationUseCase = Depends(get_delete_conversation_use_case),
) -> None:
    try:
        await use_case.execute(
            DeleteConversationCommand(conversation_id=conversation_id, user_id=current_user.id)
        )
    except ConversationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message="Conversation not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
