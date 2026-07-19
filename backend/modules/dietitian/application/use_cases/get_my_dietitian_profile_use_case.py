from uuid import UUID

from backend.modules.dietitian.application.dto.dietitian_profile_dto import DietitianProfileResult
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)


class GetMyDietitianProfileUseCase:
    def __init__(self, repository: DietitianProfileRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: UUID) -> DietitianProfileResult:
        profile = await self._repository.get_by_user_id(user_id)
        if profile is None:
            raise DietitianProfileNotFoundError("No dietitian profile found for this user.")

        return DietitianProfileResult.from_domain(profile)
