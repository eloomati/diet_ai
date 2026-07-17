from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

# Placeholder dla MongoDB client
# Uses pymongo's native async client, not Motor: Motor is deprecated by MongoDB in
# favor of PyMongo's async API, and Beanie 2.x requires it (Motor's client is
# missing driver-metadata hooks Beanie 2.x calls into).
_mongo_client: AsyncMongoClient | None = None


async def init_mongo(mongo_url: str) -> None:
    """Inicjalizuj MongoDB — będzie to wywołane w lifespan aplikacji."""
    global _mongo_client
    # tz_aware=True: PyMongo returns naive UTC datetimes by default, which
    # clashes with the rest of the app's convention (datetime.now(UTC)) and
    # produces inconsistent ISO timestamps (offset-less for values rehydrated
    # from Mongo, offset-suffixed for values still fresh from the domain
    # layer) in the same API response.
    _mongo_client = AsyncMongoClient(mongo_url, tz_aware=True)

    # Sprawdź connection
    await _mongo_client.admin.command("ping")


async def close_mongo() -> None:
    """Zamknij połączenia do MongoDB."""
    if _mongo_client:
        await _mongo_client.close()


def get_mongo_db(db_name: str = "diet_ai") -> AsyncDatabase:
    """Zwróć bazę MongoDB."""
    if not _mongo_client:
        raise RuntimeError("MongoDB nie zainicjalizowany. Wołaj init_mongo() w lifespan.")

    return _mongo_client[db_name]


async def get_mongo_session(db_name: str = "diet_ai") -> AsyncDatabase:
    """Yields instancję bazy MongoDB."""
    return get_mongo_db(db_name)


async def init_beanie_documents(document_models: list[type[Document]], db_name: str = "diet_ai") -> None:
    """Zarejestruj modele Beanie — wołane w lifespan aplikacji, po init_mongo()."""
    await init_beanie(database=get_mongo_db(db_name), document_models=document_models)
