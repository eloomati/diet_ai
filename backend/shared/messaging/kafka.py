from aiokafka import AIOKafkaProducer

# Module-level singleton, same shape as backend/shared/database/postgres.py's
# engine/sessionmaker — initialized in the app's lifespan, not per-request.
_producer: AIOKafkaProducer | None = None


async def init_kafka_producer(bootstrap_servers: str) -> None:
    """Inicjalizuj producenta Kafka — wołane w lifespan aplikacji."""
    global _producer

    _producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
    await _producer.start()


async def close_kafka_producer() -> None:
    """Zamknij połączenie producenta Kafka."""
    global _producer

    if _producer is not None:
        await _producer.stop()
        _producer = None


def get_kafka_producer() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Kafka producer nie zainicjalizowany. Wołaj init_kafka_producer() w lifespan.")
    return _producer
