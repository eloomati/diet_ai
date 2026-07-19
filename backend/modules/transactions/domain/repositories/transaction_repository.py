from abc import ABC, abstractmethod
from uuid import UUID

from backend.modules.transactions.domain.entities.transaction import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user_id(self, user_id: UUID) -> list[Transaction]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_dietitian_id(self, dietitian_id: UUID) -> list[Transaction]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self) -> list[Transaction]:
        raise NotImplementedError

    @abstractmethod
    async def save(self, transaction: Transaction) -> None:
        raise NotImplementedError
