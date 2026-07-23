from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.dietitian.api.dependencies import (
    get_list_dietitians_use_case,
    get_public_dietitian_profile_use_case,
)
from backend.modules.dietitian.api.schemas import (
    DietitianListingItemResponse,
    PublicDietitianProfileResponse,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_public_dietitian_profile_use_case import (
    GetPublicDietitianProfileUseCase,
)
from backend.modules.dietitian.application.use_cases.list_dietitians_use_case import (
    ListDietitiansUseCase,
)
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/dietitian", tags=["dietitian"])


@router.get("", response_model=list[DietitianListingItemResponse], status_code=status.HTTP_200_OK)
async def list_dietitians(
    use_case: ListDietitiansUseCase = Depends(get_list_dietitians_use_case),
) -> list[DietitianListingItemResponse]:
    results = await use_case.execute()
    return [DietitianListingItemResponse.from_result(result) for result in results]


@router.get(
    "/{dietitian_id}",
    response_model=PublicDietitianProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def get_public_dietitian_profile(
    dietitian_id: UUID,
    use_case: GetPublicDietitianProfileUseCase = Depends(get_public_dietitian_profile_use_case),
) -> PublicDietitianProfileResponse:
    try:
        result = await use_case.execute(dietitian_id)
    except DietitianProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return PublicDietitianProfileResponse.from_result(result)
