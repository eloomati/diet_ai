from uuid import UUID

from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)
from backend.modules.identity.domain.repositories.user_repository import UserRepository


class GetMyTransactionsAsDietitianUseCase:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        user_repository: UserRepository,
    ) -> None:
        self._transaction_repository = transaction_repository
        self._user_repository = user_repository

    async def execute(self, dietitian_id: UUID) -> list[TransactionResult]:
        transactions = await self._transaction_repository.list_by_dietitian_id(dietitian_id)

        results = []
        for transaction in transactions:
            # The Etap 5 "contact reveal" — a synchronous property of the
            # transaction's own current status, not of whether the Kafka
            # consumer has processed the TransactionPaid event yet (that
            # event only produces the Notification badge). Reversible:
            # mark_unpaid hides it again on the next fetch, same as
            # everything else about this 2-state toggle.
            buyer_email = None
            if transaction.status == TransactionStatus.PAID:
                buyer = await self._user_repository.get_by_id(transaction.user_id)
                buyer_email = buyer.email.value if buyer else None
            results.append(TransactionResult.from_domain(transaction, buyer_email=buyer_email))

        return results
