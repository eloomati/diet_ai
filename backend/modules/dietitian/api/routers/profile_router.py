from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.modules.dietitian.api.dependencies import (
    get_my_dietitian_profile_use_case,
    get_remove_dietitian_profile_photo_use_case,
    get_update_dietitian_profile_use_case,
    get_upload_dietitian_profile_photo_use_case,
)
from backend.modules.dietitian.api.schemas import DietitianProfileResponse, UpdateDietitianProfileRequest
from backend.modules.dietitian.application.dto.dietitian_profile_dto import (
    UpdateDietitianProfileCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.get_my_dietitian_profile_use_case import (
    GetMyDietitianProfileUseCase,
)
from backend.modules.dietitian.application.use_cases.remove_dietitian_profile_photo_use_case import (
    RemoveDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.application.use_cases.update_dietitian_profile_use_case import (
    UpdateDietitianProfileUseCase,
)
from backend.modules.dietitian.application.use_cases.upload_dietitian_profile_photo_use_case import (
    UploadDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidDietitianProfileError,
    PhotoLimitExceededError,
)
from backend.modules.identity.api.dependencies import require_role
from backend.modules.identity.domain import Role, User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/dietitian/profile", tags=["dietitian"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 5 * 1024 * 1024


@router.get("/me", response_model=DietitianProfileResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(require_role(Role.DIET_USER)),
    use_case: GetMyDietitianProfileUseCase = Depends(get_my_dietitian_profile_use_case),
) -> DietitianProfileResponse:
    try:
        result = await use_case.execute(current_user.id)
    except DietitianProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc

    return DietitianProfileResponse.from_result(result)


@router.put("", response_model=DietitianProfileResponse, status_code=status.HTTP_200_OK)
async def update_profile(
    request: UpdateDietitianProfileRequest,
    current_user: User = Depends(require_role(Role.DIET_USER)),
    use_case: UpdateDietitianProfileUseCase = Depends(get_update_dietitian_profile_use_case),
) -> DietitianProfileResponse:
    try:
        result = await use_case.execute(
            UpdateDietitianProfileCommand(
                user_id=current_user.id,
                experience=request.experience,
                diplomas=tuple(request.diplomas) if request.diplomas is not None else None,
                description=request.description,
                first_name=request.first_name,
                last_name=request.last_name,
            )
        )
    except DietitianProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except InvalidDietitianProfileError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return DietitianProfileResponse.from_result(result)


@router.post(
    "/photos",
    response_model=DietitianProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(Role.DIET_USER)),
    use_case: UploadDietitianProfilePhotoUseCase = Depends(get_upload_dietitian_profile_photo_use_case),
) -> DietitianProfileResponse:
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="Only JPEG, PNG or WEBP photos are allowed.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    content = await file.read()
    if len(content) > _MAX_PHOTO_BYTES:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message="Photo must be at most 5 MB.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = await use_case.execute(current_user.id, file.filename or "photo", content)
    except DietitianProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except PhotoLimitExceededError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return DietitianProfileResponse.from_result(result)


@router.delete(
    "/photos/{index}",
    response_model=DietitianProfileResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_profile_photo(
    index: int,
    current_user: User = Depends(require_role(Role.DIET_USER)),
    use_case: RemoveDietitianProfilePhotoUseCase = Depends(get_remove_dietitian_profile_photo_use_case),
) -> DietitianProfileResponse:
    try:
        result = await use_case.execute(current_user.id, index)
    except DietitianProfileNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND,
            message=str(exc),
            status_code=status.HTTP_404_NOT_FOUND,
        ) from exc
    except InvalidDietitianProfileError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST,
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        ) from exc

    return DietitianProfileResponse.from_result(result)
