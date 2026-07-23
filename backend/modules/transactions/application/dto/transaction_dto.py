from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)


@dataclass(frozen=True, slots=True)
class CreateTransactionCommand:
    user_id: UUID
    dietitian_id: UUID
    offer_type: OfferType


@dataclass(frozen=True, slots=True)
class TransactionResult:
    id: UUID
    user_id: UUID
    dietitian_id: UUID | None
    offer_type: OfferType
    amount: Decimal
    status: TransactionStatus
    created_at: datetime
    paid_at: datetime | None
    # Only ever populated for the dietitian's own sales view
    # (GetMyTransactionsAsDietitianUseCase), and only once status == PAID —
    # the Etap 5 "contact reveal", resolved via UserRepository at the use
    # case layer, not stored on Transaction itself. None everywhere else
    # (the buyer's own purchases, the buyer's own create-transaction
    # response, admin's listing) since those views don't need it.
    buyer_email: str | None = None

    @classmethod
    def from_domain(
        cls, transaction: Transaction, buyer_email: str | None = None
    ) -> "TransactionResult":
        return cls(
            id=transaction.id,
            user_id=transaction.user_id,
            dietitian_id=transaction.dietitian_id,
            offer_type=transaction.offer_type,
            amount=transaction.amount,
            status=transaction.status,
            created_at=transaction.created_at,
            paid_at=transaction.paid_at,
            buyer_email=buyer_email,
        )
