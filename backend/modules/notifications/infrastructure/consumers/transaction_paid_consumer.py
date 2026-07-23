from uuid import UUID

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
from backend.shared.messaging import run_kafka_consumer_loop


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
    Notification row. Started only when `kafka_provider=kafka` (see
    main.py's lifespan) — its own consumer group
    (`kafka_notifications_consumer_group_id`), independent of
    `messaging`'s own consumer on the same topic (Etap 5 Stage 2) — each
    interested module reacts to the shared event on its own terms. Note
    this consumer is *not* what reveals the buyer's contact to the
    dietitian — that's a synchronous property of `transaction.status ==
    PAID` (`GetMyTransactionsAsDietitianUseCase`), so a slow or briefly-
    down consumer never blocks that reveal; this loop only produces the
    badge."""
    await run_kafka_consumer_loop(
        topics=[settings.kafka_transaction_paid_topic],
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.kafka_notifications_consumer_group_id,
        handle_message=_handle_transaction_paid_message,
    )
