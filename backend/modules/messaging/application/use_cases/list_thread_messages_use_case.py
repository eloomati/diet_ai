from uuid import UUID

from backend.modules.messaging.application.dto.messaging_dto import DietitianMessageResult
from backend.modules.messaging.application.use_cases.exceptions import (
    ThreadAccessDeniedError,
    ThreadNotFoundError,
)
from backend.modules.messaging.domain.repositories.dietitian_message_repository import (
    DietitianMessageRepository,
)
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)


class ListThreadMessagesUseCase:
    def __init__(
        self,
        thread_repository: DietitianThreadRepository,
        message_repository: DietitianMessageRepository,
    ) -> None:
        self._thread_repository = thread_repository
        self._message_repository = message_repository

    async def execute(self, thread_id: UUID, caller_id: UUID) -> list[DietitianMessageResult]:
        thread = await self._thread_repository.get_by_id(thread_id)
        if thread is None:
            raise ThreadNotFoundError("Thread not found.")
        if not thread.has_participant(caller_id):
            raise ThreadAccessDeniedError("You are not a participant of this thread.")

        messages = await self._message_repository.list_by_thread_id(thread_id)
        return [DietitianMessageResult.from_domain(m) for m in messages]
