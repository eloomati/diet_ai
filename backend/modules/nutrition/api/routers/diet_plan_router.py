from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.modules.nutrition.api.dependencies import (
    get_diet_plan_use_case,
    get_download_diet_plan_export_use_case,
    get_export_diet_plan_use_case,
    get_generate_diet_plan_use_case,
    get_list_diet_plan_exports_use_case,
    get_list_diet_plans_use_case,
    get_rename_diet_plan_use_case,
    get_reschedule_meal_use_case,
)
from backend.modules.nutrition.api.schemas import (
    DietPlanExportResponse,
    DietPlanResponse,
    DietPlanSummaryResponse,
    GenerateDietPlanRequest,
    RenameDietPlanRequest,
    RescheduleMealRequest,
)
from backend.modules.nutrition.application import (
    DietPlanExportNotFoundError,
    DietPlanNotFoundError,
    DownloadDietPlanExportQuery,
    DownloadDietPlanExportUseCase,
    ExportDietPlanCommand,
    ExportDietPlanUseCase,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    GetDietPlanQuery,
    GetDietPlanUseCase,
    ListDietPlanExportsQuery,
    ListDietPlanExportsUseCase,
    ListDietPlansQuery,
    ListDietPlansUseCase,
    NutritionProfileNotFoundError,
    RenameDietPlanCommand,
    RenameDietPlanUseCase,
    RescheduleMealCommand,
    RescheduleMealUseCase,
)
from backend.modules.nutrition.domain import MealNotFoundError
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/diet-plans", tags=["nutrition"])


@router.post("/generate", response_model=DietPlanResponse, status_code=status.HTTP_201_CREATED)
async def generate_diet_plan(
    request: GenerateDietPlanRequest,
    current_user: User = Depends(get_current_user),
    use_case: GenerateDietPlanUseCase = Depends(get_generate_diet_plan_use_case),
) -> DietPlanResponse:
    try:
        result = await use_case.execute(
            GenerateDietPlanCommand(
                user_id=current_user.id,
                duration_days=request.duration_days,
                requirements=request.requirements,
            )
        )
    except NutritionProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietPlanResponse.from_result(result)


@router.get("", response_model=list[DietPlanSummaryResponse], status_code=status.HTTP_200_OK)
async def list_diet_plans(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    current_user: User = Depends(get_current_user),
    use_case: ListDietPlansUseCase = Depends(get_list_diet_plans_use_case),
) -> list[DietPlanSummaryResponse]:
    if from_date is not None and to_date is not None and from_date > to_date:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="'from' must not be after 'to'.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    results = await use_case.execute(
        ListDietPlansQuery(user_id=current_user.id, start_date=from_date, end_date=to_date)
    )
    return [DietPlanSummaryResponse.from_result(result) for result in results]


@router.get("/{diet_plan_id}", response_model=DietPlanResponse, status_code=status.HTTP_200_OK)
async def get_diet_plan(
    diet_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: GetDietPlanUseCase = Depends(get_diet_plan_use_case),
) -> DietPlanResponse:
    try:
        result = await use_case.execute(GetDietPlanQuery(user_id=current_user.id, plan_id=diet_plan_id))
    except DietPlanNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietPlanResponse.from_result(result)


@router.patch("/{diet_plan_id}", response_model=DietPlanResponse, status_code=status.HTTP_200_OK)
async def rename_diet_plan(
    diet_plan_id: UUID,
    request: RenameDietPlanRequest,
    current_user: User = Depends(get_current_user),
    use_case: RenameDietPlanUseCase = Depends(get_rename_diet_plan_use_case),
) -> DietPlanResponse:
    try:
        result = await use_case.execute(
            RenameDietPlanCommand(user_id=current_user.id, plan_id=diet_plan_id, name=request.name)
        )
    except DietPlanNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietPlanResponse.from_result(result)


@router.patch("/{diet_plan_id}/meals", response_model=DietPlanResponse, status_code=status.HTTP_200_OK)
async def reschedule_meal(
    diet_plan_id: UUID,
    request: RescheduleMealRequest,
    current_user: User = Depends(get_current_user),
    use_case: RescheduleMealUseCase = Depends(get_reschedule_meal_use_case),
) -> DietPlanResponse:
    try:
        result = await use_case.execute(
            RescheduleMealCommand(
                user_id=current_user.id,
                plan_id=diet_plan_id,
                day_number=request.day_number,
                meal_name=request.meal_name,
                new_time=request.new_time,
                new_day_number=request.new_day_number,
            )
        )
    except DietPlanNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except MealNotFoundError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return DietPlanResponse.from_result(result)


@router.post(
    "/{diet_plan_id}/export", response_model=DietPlanExportResponse, status_code=status.HTTP_201_CREATED
)
async def export_diet_plan(
    diet_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ExportDietPlanUseCase = Depends(get_export_diet_plan_use_case),
) -> DietPlanExportResponse:
    try:
        result = await use_case.execute(
            ExportDietPlanCommand(user_id=current_user.id, plan_id=diet_plan_id)
        )
    except DietPlanNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietPlanExportResponse.from_result(result)


@router.get(
    "/{diet_plan_id}/exports",
    response_model=list[DietPlanExportResponse],
    status_code=status.HTTP_200_OK,
)
async def list_diet_plan_exports(
    diet_plan_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: ListDietPlanExportsUseCase = Depends(get_list_diet_plan_exports_use_case),
) -> list[DietPlanExportResponse]:
    try:
        results = await use_case.execute(
            ListDietPlanExportsQuery(user_id=current_user.id, plan_id=diet_plan_id)
        )
    except DietPlanNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return [DietPlanExportResponse.from_result(result) for result in results]


@router.get("/{diet_plan_id}/exports/{export_id}/download", status_code=status.HTTP_200_OK)
async def download_diet_plan_export(
    diet_plan_id: UUID,
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    use_case: DownloadDietPlanExportUseCase = Depends(get_download_diet_plan_export_use_case),
) -> Response:
    try:
        content = await use_case.execute(
            DownloadDietPlanExportQuery(
                user_id=current_user.id, plan_id=diet_plan_id, export_id=export_id
            )
        )
    except DietPlanExportNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return Response(
        content=content.content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{content.filename}"'},
    )
