from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api_router import api_router
from backend.shared.config import get_settings
from backend.shared.database import close_mongo, close_postgres, init_mongo, init_postgres
from backend.shared.exceptions import register_exception_handlers
from backend.shared.logging import setup_logging
from backend.shared.middleware import RequestIdMiddleware
from backend.shared.providers import create_di_container


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and Shutdown events."""
    settings = get_settings()

    # === Startup ===
    try:
        await init_postgres(settings.postgres_url)
        await init_mongo(settings.mongo_url)
    except Exception as e:
        import logging
        logging.error(f"Failed to initialize databases: {e}")
        raise

    yield

    # === Shutdown ===
    await close_postgres()
    await close_mongo()


def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    # DI Container
    di_container = create_di_container(use_mock_ai=settings.use_mock_ai)
    app.state.di_container = di_container

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get(f"{settings.api_prefix}/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()