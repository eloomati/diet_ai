from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.identity.api.dependencies import get_change_user_role_use_case, require_role
from backend.modules.identity.api.schemas import ChangeUserRoleRequest, ChangeUserRoleResponse
from backend.modules.identity.application import (
    ChangeUserRoleCommand,
    ChangeUserRoleUseCase,
    UserNotFoundError,
)
from backend.modules.identity.domain import Role, User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/admin", tags=["identity-admin"])


@router.patch(
    "/users/{user_id}/role",
    response_model=ChangeUserRoleResponse,
    status_code=status.HTTP_200_OK,
)
async def change_user_role(
    user_id: UUID,
    request: ChangeUserRoleRequest,
    _caller: User = Depends(require_role(Role.SUPER_ADMIN)),
    use_case: ChangeUserRoleUseCase = Depends(get_change_user_role_use_case),
) -> ChangeUserRoleResponse:
    try:
        user = await use_case.execute(ChangeUserRoleCommand(user_id=user_id, new_role=request.new_role))
    except UserNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return ChangeUserRoleResponse(
        user_id=str(user.id),
        email=user.email.value,
        role=user.role.value,
    )
