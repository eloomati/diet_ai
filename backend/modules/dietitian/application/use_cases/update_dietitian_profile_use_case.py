from backend.modules.dietitian.application.dto.dietitian_profile_dto import (
    DietitianProfileResult,
    UpdateDietitianProfileCommand,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianProfileNotFoundError,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)


class UpdateDietitianProfileUseCase:
    def __init__(self, repository: DietitianProfileRepository) -> None:
        self._repository = repository

    async def execute(self, command: UpdateDietitianProfileCommand) -> DietitianProfileResult:
        profile = await self._repository.get_by_user_id(command.user_id)
        if profile is None:
            raise DietitianProfileNotFoundError("No dietitian profile found for this user.")

        profile.update_details(
            experience=command.experience,
            diplomas=command.diplomas,
            description=command.description,
        )
        await self._repository.save(profile)

        return DietitianProfileResult.from_domain(profile)
