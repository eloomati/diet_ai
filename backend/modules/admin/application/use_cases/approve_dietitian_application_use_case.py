from uuid import UUID

from backend.modules.dietitian.application.dto.dietitian_application_dto import (
    DietitianApplicationResult,
)
from backend.modules.dietitian.application.use_cases.exceptions import (
    DietitianApplicationNotFoundError,
)
from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.identity.application.use_cases.exceptions import UserNotFoundError
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.role import Role


class ApproveDietitianApplicationUseCase:
    def __init__(
        self,
        application_repository: DietitianApplicationRepository,
        profile_repository: DietitianProfileRepository,
        user_repository: UserRepository,
    ) -> None:
        self._application_repository = application_repository
        self._profile_repository = profile_repository
        self._user_repository = user_repository

    async def execute(self, application_id: UUID, reviewed_by: UUID) -> DietitianApplicationResult:
        application = await self._application_repository.get_by_id(application_id)
        if application is None:
            raise DietitianApplicationNotFoundError("Dietitian application not found.")

        # Raises ApplicationAlreadyReviewedError if this application was
        # already approved/rejected — a genuine entity invariant, not
        # re-checked here.
        application.approve(reviewed_by)
        await self._application_repository.save(application)

        user = await self._user_repository.get_by_id(application.user_id)
        if user is None:
            raise UserNotFoundError("The applicant's user account no longer exists.")
        user.change_role(Role.DIET_USER)
        await self._user_repository.save(user)

        # Defensive, not expected in practice: one application per user,
        # ever, and it can only be approved once — but manual DB fixes (e.g.
        # during local testing) could leave a profile already in place.
        existing_profile = await self._profile_repository.get_by_user_id(application.user_id)
        if existing_profile is None:
            profile = DietitianProfile.create(
                user_id=application.user_id,
                experience=application.experience,
                diplomas=application.diplomas,
                description=application.description,
            )
            await self._profile_repository.save(profile)

        return DietitianApplicationResult.from_domain(application)
