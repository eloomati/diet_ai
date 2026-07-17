from abc import ABC, abstractmethod
from datetime import datetime

from backend.modules.identity.domain.entities.email_log import EmailLog


class EmailLogRepository(ABC):
    @abstractmethod
    async def save(self, log: EmailLog) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_due_for_retry(self, now: datetime, limit: int = 50) -> list[EmailLog]:
        raise NotImplementedError
