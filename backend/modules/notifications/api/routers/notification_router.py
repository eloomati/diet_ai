from fastapi import APIRouter, Depends, status

from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.modules.notifications.api.dependencies import (
    get_list_my_notifications_use_case,
    get_mark_all_notifications_read_use_case,
)
from backend.modules.notifications.api.schemas import NotificationResponse
from backend.modules.notifications.application.use_cases.list_my_notifications_use_case import (
    ListMyNotificationsUseCase,
)
from backend.modules.notifications.application.use_cases.mark_all_notifications_read_use_case import (
    MarkAllNotificationsReadUseCase,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse], status_code=status.HTTP_200_OK)
async def list_my_notifications(
    current_user: User = Depends(get_current_user),
    use_case: ListMyNotificationsUseCase = Depends(get_list_my_notifications_use_case),
) -> list[NotificationResponse]:
    results = await use_case.execute(current_user.id)
    return [NotificationResponse.from_result(result) for result in results]


@router.post(
    "/mark-all-read", response_model=list[NotificationResponse], status_code=status.HTTP_200_OK
)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    use_case: MarkAllNotificationsReadUseCase = Depends(get_mark_all_notifications_read_use_case),
) -> list[NotificationResponse]:
    results = await use_case.execute(current_user.id)
    return [NotificationResponse.from_result(result) for result in results]
