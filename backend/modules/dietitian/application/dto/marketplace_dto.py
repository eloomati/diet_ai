from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from backend.modules.dietitian.application.dto.review_dto import PublicReviewResult
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.identity.domain.entities.user import User


@dataclass(frozen=True, slots=True)
class DietitianListingItemResult:
    user_id: UUID
    email: str
    experience: str
    description: str
    photos: tuple[str, ...]
    average_rating: float | None
    review_count: int

    @classmethod
    def from_domain(
        cls,
        profile: DietitianProfile,
        user: User,
        average_rating: float | None,
        review_count: int,
    ) -> "DietitianListingItemResult":
        return cls(
            user_id=profile.user_id,
            email=user.email.value,
            experience=profile.experience,
            description=profile.description,
            photos=profile.photos,
            average_rating=average_rating,
            review_count=review_count,
        )


@dataclass(frozen=True, slots=True)
class PublicDietitianProfileResult:
    user_id: UUID
    email: str
    experience: str
    diplomas: tuple[str, ...]
    description: str
    photos: tuple[str, ...]
    created_at: datetime
    average_rating: float | None
    review_count: int
    reviews: tuple[PublicReviewResult, ...]

    @classmethod
    def from_domain(
        cls,
        profile: DietitianProfile,
        user: User,
        average_rating: float | None,
        review_count: int,
        reviews: tuple[PublicReviewResult, ...],
    ) -> "PublicDietitianProfileResult":
        return cls(
            user_id=profile.user_id,
            email=user.email.value,
            experience=profile.experience,
            diplomas=profile.diplomas,
            description=profile.description,
            photos=profile.photos,
            created_at=profile.created_at,
            average_rating=average_rating,
            review_count=review_count,
            reviews=reviews,
        )
