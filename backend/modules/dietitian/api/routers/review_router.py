from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.dietitian.api.dependencies import get_submit_review_use_case
from backend.modules.dietitian.api.schemas import ReviewResponse, SubmitReviewRequest
from backend.modules.dietitian.application.dto.review_dto import SubmitReviewCommand
from backend.modules.dietitian.application.use_cases.exceptions import DietitianNotFoundError
from backend.modules.dietitian.application.use_cases.submit_review_use_case import (
    SubmitReviewUseCase,
)
from backend.modules.dietitian.domain.exceptions.dietitian_domain_errors import (
    InvalidReviewError,
    SelfReviewError,
)
from backend.modules.identity.api.dependencies import get_current_user
from backend.modules.identity.domain import User
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/dietitian", tags=["dietitian"])


@router.post(
    "/{dietitian_id}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_review(
    dietitian_id: UUID,
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    use_case: SubmitReviewUseCase = Depends(get_submit_review_use_case),
) -> ReviewResponse:
    try:
        result = await use_case.execute(
            SubmitReviewCommand(
                reviewer_id=current_user.id,
                dietitian_id=dietitian_id,
                rating=request.rating,
                comment=request.comment,
            )
        )
    except DietitianNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except SelfReviewError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=status.HTTP_400_BAD_REQUEST
        ) from exc
    except InvalidReviewError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=status.HTTP_400_BAD_REQUEST
        ) from exc

    return ReviewResponse.from_result(result)
