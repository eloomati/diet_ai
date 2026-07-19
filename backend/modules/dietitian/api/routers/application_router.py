from fastapi import APIRouter, Depends, status

from backend.modules.dietitian.api.dependencies import (
    get_my_dietitian_application_use_case,
    get_submit_dietitian_application_use_case,
)
from backend.modules.dietitian.api.schemas import (
    DietitianApplicationResponse,
    SubmitDietitianApplicationRequest,
)
from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    SubmitDietitianApplicationCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationAlreadyExistsError,
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_my_dietitian_application_use_case import (
    GetMyDietitianApplicationUseCase,
)
from backend.modules.dietitian.application.use_cases.submit_dietitian_application_use_case import (
    SubmitDietitianApplicationUseCase,
)
from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/dietitian", tags=["dietitian"])


@router.post(
    "/applications",
    response_model=DietitianApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_application(
    request: SubmitDietitianApplicationRequest,
    current_user: User = Depends(get_current_user),
    use_case: SubmitDietitianApplicationUseCase = Depends(get_submit_dietitian_application_use_case),
) -> DietitianApplicationResponse:
    try:
        result = await use_case.execute(
            SubmitDietitianApplicationCommand(
                user_id=current_user.id,
                experience=request.experience,
                diplomas=tuple(request.diplomas),
                description=request.description,
            )
        )
    except DietitianApplicationAlreadyExistsError as exc:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
        ) from exc

    return DietitianApplicationResponse.from_result(result)


@router.get(
    "/applications/me",
    response_model=DietitianApplicationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_application(
    current_user: User = Depends(get_current_user),
    use_case: GetMyDietitianApplicationUseCase = Depends(get_my_dietitian_application_use_case),
) -> DietitianApplicationResponse:
    try:
        result = await use_case.execute(current_user.id)
    except DietitianApplicationNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietitianApplicationResponse.from_result(result)
