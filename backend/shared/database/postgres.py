from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Declarative base dla ORM modeli
Base = declarative_base()

# Placeholder dla engine — będzie inicjalizowany z settingsów
_async_engine = None
_async_sessionmaker = None


async def init_postgres(database_url: str) -> None:
    """Inicjalizuj PostgreSQL — będzie to wywołane w lifespan aplikacji."""
    global _async_engine, _async_sessionmaker

    _async_engine = create_async_engine(
        database_url,
        echo=False,
        future=True,
    )
    _async_sessionmaker = sessionmaker(
        _async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def close_postgres() -> None:
    """Zamknij połączenia do PostgreSQL."""
    if _async_engine:
        await _async_engine.dispose()


@asynccontextmanager
async def get_postgres_session() -> AsyncSession:
    """Yields aktywną sesję PostgreSQL."""
    if not _async_sessionmaker:
        raise RuntimeError("PostgreSQL nie zainicjalizowany. Wołaj init_postgres() w lifespan.")

    async with _async_sessionmaker() as session:
        yield session