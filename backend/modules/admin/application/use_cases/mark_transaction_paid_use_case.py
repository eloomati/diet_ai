from uuid import UUID

from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.application.ports.transaction_event_publisher import (
    TransactionEventPublisher,
)
from backend.modules.transactions.application.use_cases.exceptions import (
    TransactionNotFoundError,
)
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)


class MarkTransactionPaidUseCase:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        event_publisher: TransactionEventPublisher,
    ) -> None:
        self._transaction_repository = transaction_repository
        self._event_publisher = event_publisher

    async def execute(self, transaction_id: UUID) -> TransactionResult:
        transaction = await self._transaction_repository.get_by_id(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("Transaction not found.")

        transaction.mark_paid()
        await self._transaction_repository.save(transaction)
        # No-op today (see NoOpTransactionEventPublisher) — a real Kafka
        # publish once Etap 5 adds that infrastructure; this use case
        # doesn't change when it does.
        await self._event_publisher.publish_transaction_paid(transaction)

        return TransactionResult.from_domain(transaction)
