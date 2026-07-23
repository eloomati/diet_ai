from backend.modules.transactions.application.ports.transaction_event_publisher import (
    TransactionEventPublisher,
)
from backend.modules.transactions.domain.entities.transaction import Transaction


class NoOpTransactionEventPublisher(TransactionEventPublisher):
    """Stand-in until Etap 5 adds real Kafka infrastructure — same
    "swappable port, mock/no-op default" shape as `EmailSender`/
    `SftpClient`/`FileStorage` elsewhere in this codebase. Records what
    it would have published (mirrors `MockEmailSender`'s `sent` list) so
    tests can assert on it without a real broker."""

    def __init__(self) -> None:
        self.published: list[Transaction] = []

    async def publish_transaction_paid(self, transaction: Transaction) -> None:
        self.published.append(transaction)
