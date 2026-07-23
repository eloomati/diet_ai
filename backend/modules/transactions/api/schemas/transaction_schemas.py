from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from backend.modules.transactions.application.dto.transaction_dto import TransactionResult
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)


class CreateTransactionRequest(BaseModel):
    dietitian_id: UUID
    offer_type: OfferType


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    dietitian_id: UUID | None
    offer_type: OfferType
    amount: Decimal
    status: TransactionStatus
    created_at: datetime
    paid_at: datetime | None
    buyer_email: str | None = None

    @classmethod
    def from_result(cls, result: TransactionResult) -> "TransactionResponse":
        return cls(
            id=result.id,
            user_id=result.user_id,
            dietitian_id=result.dietitian_id,
            offer_type=result.offer_type,
            amount=result.amount,
            status=result.status,
            created_at=result.created_at,
            paid_at=result.paid_at,
            buyer_email=result.buyer_email,
        )
