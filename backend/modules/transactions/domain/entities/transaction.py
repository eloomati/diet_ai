from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from backend.modules.transactions.domain.exceptions.transaction_domain_errors import (
    InvalidTransactionError,
)
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)

# Fixed demo-scope prices, keyed by offer — there is no admin-configurable
# pricing UI planned, and no payment gateway to source a real price from.
# Server-computed only: a create-transaction request never accepts its own
# amount from the client.
OFFER_PRICES: dict[OfferType, Decimal] = {
    OfferType.PLAN_REVIEW: Decimal("49.00"),
    OfferType.INDIVIDUAL_PLAN: Decimal("149.00"),
}


@dataclass(slots=True)
class Transaction:
    id: UUID
    user_id: UUID
    # Nullable at the DB level (ON DELETE SET NULL) — a transaction outlives
    # a since-deleted dietitian account, so this can legitimately become
    # None for an existing row even though `create()` always sets a real one.
    dietitian_id: UUID | None
    offer_type: OfferType
    amount: Decimal
    status: TransactionStatus = TransactionStatus.UNPAID
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    paid_at: datetime | None = None

    @classmethod
    def create(cls, user_id: UUID, dietitian_id: UUID, offer_type: OfferType) -> "Transaction":
        if user_id == dietitian_id:
            raise InvalidTransactionError("A user cannot buy their own offer.")

        return cls(
            id=uuid4(),
            user_id=user_id,
            dietitian_id=dietitian_id,
            offer_type=offer_type,
            amount=OFFER_PRICES[offer_type],
            status=TransactionStatus.UNPAID,
            created_at=datetime.now(UTC),
        )

    def mark_paid(self) -> None:
        # A reversible toggle, not a one-way approval — re-marking an
        # already-paid transaction paid is a no-op state, not an error.
        self.status = TransactionStatus.PAID
        self.paid_at = datetime.now(UTC)

    def mark_unpaid(self) -> None:
        self.status = TransactionStatus.UNPAID
        self.paid_at = None
