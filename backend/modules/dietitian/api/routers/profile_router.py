from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.modules.dietitian.api.dependencies import get_upload_dietitian_profile_photo_use_case
from backend.modules.dietitian.api.schemas import DietitianProfileResponse
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.application.use_cases.upload_dietitian_profile_photo_use_case import (
    UploadDietitianProfilePhotoUseCase,
)
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    PhotoLimitExceededError,
)
from backend.modules.identity.api.dependencies import require_role
from backend.modules.identity.domain import Role, User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/dietitian/profile", tags=["dietitian"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 5 * 1024 * 1024


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
