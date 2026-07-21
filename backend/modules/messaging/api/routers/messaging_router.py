from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.modules.messaging.api.dependencies import (
    get_list_my_dietitian_threads_use_case,
    get_list_thread_messages_use_case,
    get_send_dietitian_message_use_case,
)
from backend.modules.messaging.api.schemas import (
    DietitianMessageResponse,
    DietitianThreadResponse,
    SendMessageRequest,
)
from backend.modules.messaging.application.dto.messaging_dto import SendMessageCommand
from backend.modules.messaging.application.use_cases.exceptions import (
    ThreadAccessDeniedError,
    ThreadNotFoundError,
)
from backend.modules.messaging.application.use_cases.list_my_dietitian_threads_use_case import (
    ListMyDietitianThreadsUseCase,
)
from backend.modules.messaging.application.use_cases.list_thread_messages_use_case import (
    ListThreadMessagesUseCase,
)
from backend.modules.messaging.application.use_cases.send_dietitian_message_use_case import (
    SendDietitianMessageUseCase,
)
from backend.modules.messaging.domain.exceptions.messaging_domain_errors import (
    InvalidMessageError,
)
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/messaging", tags=["messaging"])


@router.get(
    "/threads", response_model=list[DietitianThreadResponse], status_code=status.HTTP_200_OK
)
async def list_my_threads(
    current_user: User = Depends(get_current_user),
    use_case: ListMyDietitianThreadsUseCase = Depends(get_list_my_dietitian_threads_use_case),
) -> list[DietitianThreadResponse]:
    results = await use_case.execute(current_user.id)
    return [DietitianThreadResponse.from_result(result) for result in results]


@router.get(
    "/threads/{thread_id}/messages",
    response_model=list[DietitianMessageResponse],
    status_code=status.HTTP_200_OK,
)
async def list_thread_messages(
    thread_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ListThreadMessagesUseCase = Depends(get_list_thread_messages_use_case),
) -> list[DietitianMessageResponse]:
    try:
        results = await use_case.execute(thread_id, current_user.id)
    except ThreadNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except ThreadAccessDeniedError as exc:
        raise AppException(
            code=ErrorCode.FORBIDDEN, message=str(exc), status_code=status.HTTP_403_FORBIDDEN
        ) from exc

    return [DietitianMessageResponse.from_result(result) for result in results]


@router.post(
    "/threads/{thread_id}/messages",
    response_model=DietitianMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    thread_id: UUID,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    use_case: SendDietitianMessageUseCase = Depends(get_send_dietitian_message_use_case),
) -> DietitianMessageResponse:
    try:
        result = await use_case.execute(
            SendMessageCommand(
                thread_id=thread_id,
                caller_id=current_user.id,
                content=request.content,
                diet_plan_id=request.diet_plan_id,
            )
        )
    except ThreadNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except ThreadAccessDeniedError as exc:
        raise AppException(
            code=ErrorCode.FORBIDDEN, message=str(exc), status_code=status.HTTP_403_FORBIDDEN
        ) from exc
    except InvalidMessageError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=status.HTTP_400_BAD_REQUEST
        ) from exc

    return DietitianMessageResponse.from_result(result)
