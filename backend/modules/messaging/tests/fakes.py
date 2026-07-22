from uuid import UUID

from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread


class InMemoryDietitianThreadRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietitianThread] = {}

    async def get_by_id(self, thread_id: UUID) -> DietitianThread | None:
        return self._by_id.get(thread_id)

    async def get_by_participants(
        self, user_id: UUID, dietitian_id: UUID
    ) -> DietitianThread | None:
        for thread in self._by_id.values():
            if thread.user_id == user_id and thread.dietitian_id == dietitian_id:
                return thread
        return None

    async def list_by_participant(self, user_id: UUID) -> list[DietitianThread]:
        threads = [
            t for t in self._by_id.values() if t.user_id == user_id or t.dietitian_id == user_id
        ]
        return sorted(threads, key=lambda t: t.created_at, reverse=True)

    async def save(self, thread: DietitianThread) -> None:
        self._by_id[thread.id] = thread


class InMemoryDietitianMessageRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietitianMessage] = {}

    async def list_by_thread_id(self, thread_id: UUID) -> list[DietitianMessage]:
        messages = [m for m in self._by_id.values() if m.thread_id == thread_id]
        return sorted(messages, key=lambda m: m.created_at)

    async def save(self, message: DietitianMessage) -> None:
        self._by_id[message.id] = message
