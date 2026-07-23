from uuid import UUID

from backend.modules.dietitian.application.dto.marketplace_dto import PublicDietitianProfileResult
from backend.modules.dietitian.application.dto.review_dto import PublicReviewResult
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.dietitian.domain.repositories.review_repository import ReviewRepository
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.domain.value_objects.user_status import UserStatus


class GetPublicDietitianProfileUseCase:
    def __init__(
        self,
        profile_repository: DietitianProfileRepository,
        user_repository: UserRepository,
        review_repository: ReviewRepository,
    ) -> None:
        self._profile_repository = profile_repository
        self._user_repository = user_repository
        self._review_repository = review_repository

    async def execute(self, dietitian_id: UUID) -> PublicDietitianProfileResult:
        profile = await self._profile_repository.get_by_user_id(dietitian_id)
        user = await self._user_repository.get_by_id(dietitian_id)

        # Treated as a single "not found" outcome regardless of which check
        # actually failed — no need to leak whether it's a missing profile,
        # a reversed role, or a ban to a public, unauthenticated caller.
        if profile is None or user is None or user.role != Role.DIET_USER or user.status != UserStatus.ACTIVE:
            raise DietitianProfileNotFoundError("No dietitian found for this id.")

        average_rating, review_count = await self._review_repository.rating_summary_by_dietitian_id(
            dietitian_id
        )
        reviews = await self._review_repository.list_by_dietitian_id(dietitian_id)
        # reviewer_id is ON DELETE CASCADE — a review can't outlive its
        # reviewer, so this lookup is never None for an existing review.
        public_reviews = []
        for review in reviews:
            reviewer = await self._user_repository.get_by_id(review.reviewer_id)
            public_reviews.append(PublicReviewResult.from_domain(review, reviewer.resolved_display_name))
        public_reviews = tuple(public_reviews)

        return PublicDietitianProfileResult.from_domain(
            profile, user, average_rating, review_count, public_reviews
        )
