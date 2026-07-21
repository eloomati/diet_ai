import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

from aiokafka import AIOKafkaConsumer

logger = logging.getLogger(__name__)


async def run_kafka_consumer_loop(
    *,
    topics: list[str],
    bootstrap_servers: str,
    group_id: str,
    handle_message: Callable[[dict], Awaitable[None]],
) -> None:
    """Generic consume loop: JSON-decodes each message and hands it to
    `handle_message`, logging (not raising) any per-message failure so one
    bad message never kills the whole background task. Runs as an
    asyncio task for the app's lifetime, same shape as
    `run_email_retry_loop` — extracted once a second, near-identical
    consumer (messaging's own reaction to `TransactionPaid`, alongside
    notifications') needed the exact same start/loop/stop boilerplate."""
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=bootstrap_servers,
        group_id=group_id,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    try:
        async for message in consumer:
            try:
                payload = json.loads(message.value.decode("utf-8"))
                await handle_message(payload)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Failed to process message on topic %s.", message.topic)
    finally:
        await consumer.stop()
