import uuid
from decimal import Decimal

import pytest

from backend.modules.transactions.domain import (
    OFFER_PRICES,
    InvalidTransactionError,
    OfferType,
    Transaction,
    TransactionStatus,
)


def _create(**overrides) -> Transaction:
    defaults = dict(
        user_id=uuid.uuid4(),
        dietitian_id=uuid.uuid4(),
        offer_type=OfferType.PLAN_REVIEW,
    )
    defaults.update(overrides)
    return Transaction.create(**defaults)


def test_create_sets_unpaid_status_and_no_paid_at() -> None:
    transaction = _create()

    assert transaction.status == TransactionStatus.UNPAID
    assert transaction.paid_at is None


def test_create_sets_amount_from_offer_price_table() -> None:
    transaction = _create(offer_type=OfferType.INDIVIDUAL_PLAN)

    assert transaction.amount == OFFER_PRICES[OfferType.INDIVIDUAL_PLAN]
    assert transaction.amount == Decimal("149.00")


def test_create_rejects_buying_your_own_offer() -> None:
    same_id = uuid.uuid4()

    with pytest.raises(InvalidTransactionError):
        Transaction.create(user_id=same_id, dietitian_id=same_id, offer_type=OfferType.PLAN_REVIEW)


def test_mark_paid_sets_status_and_paid_at() -> None:
    transaction = _create()

    transaction.mark_paid()

    assert transaction.status == TransactionStatus.PAID
    assert transaction.paid_at is not None


def test_mark_unpaid_clears_status_and_paid_at() -> None:
    transaction = _create()
    transaction.mark_paid()

    transaction.mark_unpaid()

    assert transaction.status == TransactionStatus.UNPAID
    assert transaction.paid_at is None


def test_mark_paid_is_idempotent_when_already_paid() -> None:
    transaction = _create()
    transaction.mark_paid()
    first_paid_at = transaction.paid_at

    transaction.mark_paid()

    assert transaction.status == TransactionStatus.PAID
    assert transaction.paid_at >= first_paid_at
