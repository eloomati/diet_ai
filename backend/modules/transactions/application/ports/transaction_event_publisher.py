from abc import ABC, abstractmethod

from backend.modules.transactions.domain.entities.transaction import Transaction


class TransactionEventPublisher(ABC):
    @abstractmethod
    async def publish_transaction_paid(self, transaction: Transaction) -> None:
        raise NotImplementedError
