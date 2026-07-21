from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.modules.dietitian.application.dto.marketplace_dto import (
    DietitianListingItemResult,
    PublicDietitianProfileResult,
)
from backend.modules.dietitian.application.dto.review_dto import PublicReviewResult


class DietitianListingItemResponse(BaseModel):
    user_id: UUID
    email: str
    experience: str
    description: str
    photos: list[str]
    average_rating: float | None
    review_count: int

    @classmethod
    def from_result(cls, result: DietitianListingItemResult) -> "DietitianListingItemResponse":
        return cls(
            user_id=result.user_id,
            email=result.email,
            experience=result.experience,
            description=result.description,
            photos=list(result.photos),
            average_rating=result.average_rating,
            review_count=result.review_count,
        )


class PublicReviewResponse(BaseModel):
    rating: int
    comment: str
    created_at: datetime

    @classmethod
    def from_result(cls, result: PublicReviewResult) -> "PublicReviewResponse":
        return cls(rating=result.rating, comment=result.comment, created_at=result.created_at)


class PublicDietitianProfileResponse(BaseModel):
    user_id: UUID
    email: str
    experience: str
    diplomas: list[str]
    description: str
    photos: list[str]
    created_at: datetime
    average_rating: float | None
    review_count: int
    reviews: list[PublicReviewResponse]

    @classmethod
    def from_result(cls, result: PublicDietitianProfileResult) -> "PublicDietitianProfileResponse":
        return cls(
            user_id=result.user_id,
            email=result.email,
            experience=result.experience,
            diplomas=list(result.diplomas),
            description=result.description,
            photos=list(result.photos),
            created_at=result.created_at,
            average_rating=result.average_rating,
            review_count=result.review_count,
            reviews=[PublicReviewResponse.from_result(r) for r in result.reviews],
        )
