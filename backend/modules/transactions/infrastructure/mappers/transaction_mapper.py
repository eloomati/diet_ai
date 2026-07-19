from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.domain.value_objects.transaction_status import (
    TransactionStatus,
)
from backend.modules.transactions.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)


class TransactionMapper:
    @staticmethod
    def to_domain(model: TransactionModel) -> Transaction:
        return Transaction(
            id=model.id,
            user_id=model.user_id,
            dietitian_id=model.dietitian_id,
            offer_type=OfferType(model.offer_type),
            amount=model.amount,
            status=TransactionStatus(model.status),
            created_at=model.created_at,
            paid_at=model.paid_at,
        )

    @staticmethod
    def to_model(transaction: Transaction) -> TransactionModel:
        return TransactionModel(
            id=transaction.id,
            user_id=transaction.user_id,
            dietitian_id=transaction.dietitian_id,
            offer_type=transaction.offer_type.value,
            amount=transaction.amount,
            status=transaction.status.value,
            created_at=transaction.created_at,
            paid_at=transaction.paid_at,
        )
