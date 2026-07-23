from uuid import UUID

from backend.modules.messaging.application.dto.messaging_dto import DietitianThreadResult
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)


class EnsureDietitianThreadUseCase:
    """Get-or-create — called by the Kafka consumer reacting to
    TransactionPaid, not exposed via any endpoint. One thread per
    (user_id, dietitian_id) pair, reused across every future payment
    between the same two people."""

    def __init__(self, thread_repository: DietitianThreadRepository) -> None:
        self._thread_repository = thread_repository

    async def execute(self, user_id: UUID, dietitian_id: UUID) -> DietitianThreadResult:
        existing = await self._thread_repository.get_by_participants(user_id, dietitian_id)
        if existing is not None:
            return DietitianThreadResult.from_domain(existing)

        thread = DietitianThread.create(user_id=user_id, dietitian_id=dietitian_id)
        await self._thread_repository.save(thread)
        return DietitianThreadResult.from_domain(thread)
