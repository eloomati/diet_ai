from uuid import UUID

from backend.modules.dietitian.application.services.resolve_dietitian_name import (
    resolve_dietitian_name,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.messaging.application.dto.messaging_dto import DietitianThreadResult
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)


class ListMyDietitianThreadsUseCase:
    def __init__(
        self,
        thread_repository: DietitianThreadRepository,
        user_repository: UserRepository,
        dietitian_profile_repository: DietitianProfileRepository,
    ) -> None:
        self._thread_repository = thread_repository
        self._user_repository = user_repository
        self._dietitian_profile_repository = dietitian_profile_repository

    async def execute(self, caller_id: UUID) -> list[DietitianThreadResult]:
        threads = await self._thread_repository.list_by_participant(caller_id)

        results = []
        for thread in threads:
            other_id = thread.other_participant(caller_id)
            other = await self._user_repository.get_by_id(other_id)
            other_name = None
            if other is not None:
                if other_id == thread.dietitian_id:
                    # The other side is the dietitian — real name takes
                    # priority over their generic display_name/email.
                    profile = await self._dietitian_profile_repository.get_by_user_id(other_id)
                    other_name = (
                        resolve_dietitian_name(profile, other)
                        if profile is not None
                        else other.resolved_display_name
                    )
                else:
                    other_name = other.resolved_display_name
            results.append(DietitianThreadResult.from_domain(thread, other_participant_name=other_name))
        return results
