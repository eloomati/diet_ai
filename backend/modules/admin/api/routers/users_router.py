from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.admin.api.dependencies import (
    get_activate_user_use_case,
    get_ban_user_use_case,
    get_delete_user_use_case,
    get_list_users_use_case,
)
from backend.modules.admin.api.schemas import UserSummaryResponse
from backend.modules.admin.application.use_cases.activate_user_use_case import ActivateUserUseCase
from backend.modules.admin.application.use_cases.ban_user_use_case import BanUserUseCase
from backend.modules.admin.application.use_cases.delete_user_use_case import DeleteUserUseCase
from backend.modules.admin.application.use_cases.exceptions import CannotDeleteSelfError
from backend.modules.admin.application.use_cases.list_users_use_case import ListUsersUseCase
from backend.modules.identity.api.dependencies import require_role
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain import Role, User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("", response_model=list[UserSummaryResponse], status_code=status.HTTP_200_OK)
async def list_users(
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
) -> list[UserSummaryResponse]:
    results = await use_case.execute()
    return [UserSummaryResponse.from_result(result) for result in results]


@router.post(
    "/{user_id}/activate", response_model=UserSummaryResponse, status_code=status.HTTP_200_OK
)
async def activate_user(
    user_id: UUID,
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: ActivateUserUseCase = Depends(get_activate_user_use_case),
) -> UserSummaryResponse:
    try:
        result = await use_case.execute(user_id)
    except UserNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return UserSummaryResponse.from_result(result)


@router.post("/{user_id}/ban", response_model=UserSummaryResponse, status_code=status.HTTP_200_OK)
async def ban_user(
    user_id: UUID,
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: BanUserUseCase = Depends(get_ban_user_use_case),
) -> UserSummaryResponse:
    try:
        result = await use_case.execute(user_id)
    except UserNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return UserSummaryResponse.from_result(result)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
) -> None:
    try:
        await use_case.execute(user_id, caller.id)
    except CannotDeleteSelfError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=status.HTTP_400_BAD_REQUEST
        ) from exc
    except UserNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
