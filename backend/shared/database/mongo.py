from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

# Placeholder dla MongoDB client
_mongo_client: AsyncIOMotorClient | None = None


async def init_mongo(mongo_url: str) -> None:
    """Inicjalizuj MongoDB — będzie to wywołane w lifespan aplikacji."""
    global _mongo_client
    _mongo_client = AsyncIOMotorClient(mongo_url)

    # Sprawdź connection
    await _mongo_client.admin.command("ping")


async def close_mongo() -> None:
    """Zamknij połączenia do MongoDB."""
    if _mongo_client:
        _mongo_client.close()


def get_mongo_db(db_name: str = "diet_ai") -> AsyncIOMotorDatabase:
    """Zwróć bazę MongoDB."""
    if not _mongo_client:
        raise RuntimeError("MongoDB nie zainicjalizowany. Wołaj init_mongo() w lifespan.")

    return _mongo_client[db_name]


async def get_mongo_session(db_name: str = "diet_ai") -> AsyncIOMotorDatabase:
    """Yields instancję bazy MongoDB."""
    return get_mongo_db(db_name)