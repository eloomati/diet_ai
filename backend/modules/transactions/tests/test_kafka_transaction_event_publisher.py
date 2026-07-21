import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.value_objects.offer_type import OfferType
from backend.modules.transactions.infrastructure.events.kafka_transaction_event_publisher import (
    KafkaTransactionEventPublisher,
)


class FakeKafkaProducer:
    def __init__(self) -> None:
        self.sent: list[tuple[str, bytes]] = []

    async def send_and_wait(self, topic: str, value: bytes) -> None:
        self.sent.append((topic, value))


@pytest.mark.asyncio
async def test_publish_transaction_paid_sends_the_expected_payload() -> None:
    producer = FakeKafkaProducer()
    publisher = KafkaTransactionEventPublisher(producer=producer, topic="transaction-paid")
    transaction = Transaction.create(
        user_id=uuid.uuid4(), dietitian_id=uuid.uuid4(), offer_type=OfferType.PLAN_REVIEW
    )
    transaction.mark_paid()

    await publisher.publish_transaction_paid(transaction)

    assert len(producer.sent) == 1
    topic, raw_value = producer.sent[0]
    assert topic == "transaction-paid"
    payload = json.loads(raw_value.decode("utf-8"))
    assert payload["transaction_id"] == str(transaction.id)
    assert payload["user_id"] == str(transaction.user_id)
    assert payload["dietitian_id"] == str(transaction.dietitian_id)
    assert payload["offer_type"] == "PLAN_REVIEW"
    assert payload["amount"] == "49.00"
    assert payload["paid_at"] == transaction.paid_at.isoformat()


@pytest.mark.asyncio
async def test_publish_transaction_paid_handles_a_null_dietitian_id() -> None:
    producer = FakeKafkaProducer()
    publisher = KafkaTransactionEventPublisher(producer=producer, topic="transaction-paid")
    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        dietitian_id=None,
        offer_type=OfferType.PLAN_REVIEW,
        amount=Decimal("49.00"),
        created_at=datetime.now(UTC),
    )
    transaction.mark_paid()

    await publisher.publish_transaction_paid(transaction)

    payload = json.loads(producer.sent[0][1].decode("utf-8"))
    assert payload["dietitian_id"] is None
