from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.modules.dietitian.application.dto.review_dto import ReviewResult


class SubmitReviewRequest(BaseModel):
    rating: int = Field(ge=1, le=10)
    comment: str


class ReviewResponse(BaseModel):
    id: UUID
    reviewer_id: UUID
    reviewer_name: str
    dietitian_id: UUID
    rating: int
    comment: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_result(cls, result: ReviewResult) -> "ReviewResponse":
        return cls(
            id=result.id,
            reviewer_id=result.reviewer_id,
            reviewer_name=result.reviewer_name,
            dietitian_id=result.dietitian_id,
            rating=result.rating,
            comment=result.comment,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
