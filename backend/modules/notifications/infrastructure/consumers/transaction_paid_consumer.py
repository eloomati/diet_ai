import asyncio
import json
import logging
from uuid import UUID

from aiokafka import AIOKafkaConsumer

from backend.modules.notifications.application.use_cases.create_notification_use_case import (
    CreateNotificationUseCase,
)
from backend.modules.notifications.domain.value_objects.notification_type import (
    NotificationType,
)
from backend.modules.notifications.infrastructure.persistence.repository.sqlalchemy_notification_repository import (
    SqlAlchemyNotificationRepository,
)
from backend.shared.config.settings import Settings
from backend.shared.database.postgres import get_postgres_session

logger = logging.getLogger(__name__)


async def _handle_transaction_paid_message(payload: dict) -> None:
    dietitian_id = payload.get("dietitian_id")
    if dietitian_id is None:
        # The dietitian's account was already deleted by the time this
        # message is consumed (Transaction.dietitian_id is ON DELETE SET
        # NULL) — no one left to notify or reveal a buyer's contact to.
        return

    async with get_postgres_session() as session:
        repository = SqlAlchemyNotificationRepository(session)
        use_case = CreateNotificationUseCase(repository)
        await use_case.execute(
            recipient_user_id=UUID(dietitian_id),
            type=NotificationType.TRANSACTION_PAID,
            reference_id=UUID(payload["transaction_id"]),
        )
        await session.commit()


async def run_transaction_paid_consumer(settings: Settings) -> None:
    """Background task: consumes TransactionPaid events published by
    `KafkaTransactionEventPublisher` and creates the dietitian-facing
    Notification row. Runs as an asyncio task for the app's lifetime,
    same shape as `run_email_retry_loop` — started only when
    `kafka_provider=kafka` (see main.py's lifespan). Note this consumer
    is *not* what reveals the buyer's contact to the dietitian — that's a
    synchronous property of `transaction.status == PAID`
    (`GetMyTransactionsAsDietitianUseCase`), so a slow or briefly-down
    consumer never blocks that reveal; this loop only produces the badge.
    """
    consumer = AIOKafkaConsumer(
        settings.kafka_transaction_paid_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_consumer_group_id,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                payload = json.loads(message.value.decode("utf-8"))
                await _handle_transaction_paid_message(payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Failed to process TransactionPaid message.")
    finally:
        await consumer.stop()
