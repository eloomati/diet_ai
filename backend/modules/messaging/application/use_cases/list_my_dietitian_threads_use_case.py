from uuid import UUID

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
    ) -> None:
        self._thread_repository = thread_repository
        self._user_repository = user_repository

    async def execute(self, caller_id: UUID) -> list[DietitianThreadResult]:
        threads = await self._thread_repository.list_by_participant(caller_id)

        results = []
        for thread in threads:
            other_id = thread.other_participant(caller_id)
            other = await self._user_repository.get_by_id(other_id)
            results.append(
                DietitianThreadResult.from_domain(
                    thread, other_participant_email=other.email.value if other else None
                )
            )
        return results
