from fastapi import APIRouter, Depends, status

from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.modules.nutrition.api.dependencies import (
    get_create_nutrition_profile_use_case,
    get_nutrition_profile_use_case,
    get_update_nutrition_profile_use_case,
)
from backend.modules.nutrition.api.schemas import (
    CreateNutritionProfileRequest,
    NutritionProfileResponse,
    UpdateNutritionProfileRequest,
    WeeklyObligationRequest,
)
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    GetNutritionProfileQuery,
    GetNutritionProfileUseCase,
    NutritionProfileAlreadyExistsError,
    NutritionProfileNotFoundError,
    UpdateNutritionProfileCommand,
    UpdateNutritionProfileUseCase,
    WeeklyObligationInput,
)
from backend.modules.nutrition.domain import InvalidWeeklyObligationError
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/profile", tags=["nutrition"])


def _to_obligation_input(obligation: WeeklyObligationRequest) -> WeeklyObligationInput:
    return WeeklyObligationInput(
        day_of_week=obligation.day_of_week.value,
        start_time=obligation.start_time.isoformat(timespec="minutes"),
        end_time=obligation.end_time.isoformat(timespec="minutes"),
        label=obligation.label,
    )


@router.post("", response_model=NutritionProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    request: CreateNutritionProfileRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateNutritionProfileUseCase = Depends(get_create_nutrition_profile_use_case),
) -> NutritionProfileResponse:
    try:
        result = await use_case.execute(
            CreateNutritionProfileCommand(
                user_id=current_user.id,
                age=request.age,
                height_cm=request.height_cm,
                weight_kg=request.weight_kg,
                activity_level=request.activity_level.value,
                goal=request.goal.value,
                diet_type=request.diet_type.value,
                weekly_obligations=tuple(
                    _to_obligation_input(o) for o in request.weekly_obligations
                ),
            )
        )
    except NutritionProfileAlreadyExistsError as exc:
        raise AppException(
            code=ErrorCode.CONFLICT,
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
        ) from exc
    except InvalidWeeklyObligationError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return NutritionProfileResponse.from_result(result)


@router.get("", response_model=NutritionProfileResponse, status_code=status.HTTP_200_OK)
async def get_profile(
    current_user: User = Depends(get_current_user),
    use_case: GetNutritionProfileUseCase = Depends(get_nutrition_profile_use_case),
) -> NutritionProfileResponse:
    try:
        result = await use_case.execute(GetNutritionProfileQuery(user_id=current_user.id))
    except NutritionProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return NutritionProfileResponse.from_result(result)


@router.put("", response_model=NutritionProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    request: UpdateNutritionProfileRequest,
    current_user: User = Depends(get_current_user),
    use_case: UpdateNutritionProfileUseCase = Depends(get_update_nutrition_profile_use_case),
) -> NutritionProfileResponse:
    try:
        result = await use_case.execute(
            UpdateNutritionProfileCommand(
                user_id=current_user.id,
                age=request.age,
                height_cm=request.height_cm,
                weight_kg=request.weight_kg,
                activity_level=request.activity_level.value if request.activity_level else None,
                goal=request.goal.value if request.goal else None,
                diet_type=request.diet_type.value if request.diet_type else None,
                weekly_obligations=(
                    tuple(_to_obligation_input(o) for o in request.weekly_obligations)
                    if request.weekly_obligations is not None
                    else None
                ),
            )
        )
    except NutritionProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except InvalidWeeklyObligationError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return NutritionProfileResponse.from_result(result)
