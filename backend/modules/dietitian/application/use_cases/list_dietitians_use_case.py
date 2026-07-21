from backend.modules.dietitian.application.dto.marketplace_dto import DietitianListingItemResult
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.dietitian.domain.repositories.review_repository import ReviewRepository
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.role import Role
from backend.modules.identity.domain.value_objects.user_status import UserStatus


class ListDietitiansUseCase:
    def __init__(
        self,
        profile_repository: DietitianProfileRepository,
        user_repository: UserRepository,
        review_repository: ReviewRepository,
    ) -> None:
        self._profile_repository = profile_repository
        self._user_repository = user_repository
        self._review_repository = review_repository

    async def execute(self) -> list[DietitianListingItemResult]:
        profiles = await self._profile_repository.list_all()

        items: list[DietitianListingItemResult] = []
        for profile in profiles:
            user = await self._user_repository.get_by_id(profile.user_id)
            # A profile whose owner is no longer an active DIET_USER (role
            # reversed by a SUPER_ADMIN, or banned) shouldn't be discoverable
            # — same role/status check CreateTransactionUseCase already
            # applies when validating a purchase target.
            if user is None or user.role != Role.DIET_USER or user.status != UserStatus.ACTIVE:
                continue

            average_rating, review_count = (
                await self._review_repository.rating_summary_by_dietitian_id(profile.user_id)
            )
            items.append(
                DietitianListingItemResult.from_domain(profile, user, average_rating, review_count)
            )

        return items
