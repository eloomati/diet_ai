import json
from typing import Protocol

from backend.modules.transactions.application.ports.transaction_event_publisher import (
    TransactionEventPublisher,
)
from backend.modules.transactions.domain.entities.transaction import Transaction


class _KafkaProducerLike(Protocol):
    """Just the one method this class actually calls — lets tests pass a
    fake without needing a real aiokafka.AIOKafkaProducer instance."""

    async def send_and_wait(self, topic: str, value: bytes) -> object: ...


class KafkaTransactionEventPublisher(TransactionEventPublisher):
    """Real implementation of the port `NoOpTransactionEventPublisher` stood
    in for since Etap 3 — this use case (`MarkTransactionPaidUseCase`)
    itself doesn't change now that Etap 5 adds Kafka, exactly per that
    stand-in's own original design. Takes the producer as a constructor
    dependency (same convention as every SqlAlchemyXRepository taking its
    session) rather than reaching into the shared singleton itself — the
    DI wiring layer resolves `get_kafka_producer()`, not this class."""

    def __init__(self, producer: _KafkaProducerLike, topic: str) -> None:
        self._producer = producer
        self._topic = topic

    async def publish_transaction_paid(self, transaction: Transaction) -> None:
        payload = {
            "transaction_id": str(transaction.id),
            "user_id": str(transaction.user_id),
            "dietitian_id": str(transaction.dietitian_id) if transaction.dietitian_id else None,
            "offer_type": transaction.offer_type.value,
            "amount": str(transaction.amount),
            "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None,
        }
        await self._producer.send_and_wait(self._topic, json.dumps(payload).encode("utf-8"))
