from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.modules.admin.api.dependencies import (
    get_approve_dietitian_application_use_case,
    get_list_dietitian_applications_use_case,
    get_reject_dietitian_application_use_case,
)
from backend.modules.admin.api.schemas import Page
from backend.modules.admin.application.use_cases.approve_dietitian_application_use_case import (
    ApproveDietitianApplicationUseCase,
)
from backend.modules.admin.application.use_cases.list_dietitian_applications_use_case import (
    ListDietitianApplicationsUseCase,
)
from backend.modules.admin.application.use_cases.reject_dietitian_application_use_case import (
    RejectDietitianApplicationUseCase,
)
from backend.modules.dietitian.api.schemas import DietitianApplicationResponse
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    ApplicationAlreadyReviewedError,
)
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus
from backend.modules.identity.api.dependencies import require_role
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain import Role, User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/admin/dietitian-applications", tags=["admin"])


@router.get(
    "", response_model=Page[DietitianApplicationResponse], status_code=status.HTTP_200_OK
)
async def list_dietitian_applications(
    status_filter: ApplicationStatus | None = Query(None, alias="status"),
    limit: int | None = Query(default=None, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: ListDietitianApplicationsUseCase = Depends(
        get_list_dietitian_applications_use_case
    ),
) -> Page[DietitianApplicationResponse]:
    page = await use_case.execute(status_filter, limit=limit, offset=offset)
    return Page(
        items=[DietitianApplicationResponse.from_result(result) for result in page.items],
        total=page.total,
    )


@router.post(
    "/{application_id}/approve",
    response_model=DietitianApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_dietitian_application(
    application_id: UUID,
    caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: ApproveDietitianApplicationUseCase = Depends(
        get_approve_dietitian_application_use_case
    ),
) -> DietitianApplicationResponse:
    try:
        result = await use_case.execute(application_id, caller.id)
    except DietitianApplicationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except ApplicationAlreadyReviewedError as exc:
        raise AppException(
            code=ErrorCode.CONFLICT, message=str(exc), status_code=status.HTTP_409_CONFLICT
        ) from exc
    except UserNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return DietitianApplicationResponse.from_result(result)


@router.post(
    "/{application_id}/reject",
    response_model=DietitianApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def reject_dietitian_application(
    application_id: UUID,
    caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: RejectDietitianApplicationUseCase = Depends(
        get_reject_dietitian_application_use_case
    ),
) -> DietitianApplicationResponse:
    try:
        result = await use_case.execute(application_id, caller.id)
    except DietitianApplicationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except ApplicationAlreadyReviewedError as exc:
        raise AppException(
            code=ErrorCode.CONFLICT, message=str(exc), status_code=status.HTTP_409_CONFLICT
        ) from exc

    return DietitianApplicationResponse.from_result(result)
