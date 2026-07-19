import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api_router import api_router
from backend.modules.ai.infrastructure import close_llm_provider, init_llm_provider
from backend.modules.conversation.infrastructure.documents import ConversationDocument
from backend.modules.identity.infrastructure.email.email_retry_scheduler import run_email_retry_loop
from backend.modules.nutrition.infrastructure.documents import (
    DietPlanDocument,
    DietPlanExportDocument,
    NutritionProfileDocument,
)
from backend.shared.config import get_settings
from backend.shared.database import (
    close_mongo,
    close_postgres,
    init_beanie_documents,
    init_mongo,
    init_postgres,
)
from backend.shared.exceptions import register_exception_handlers
from backend.shared.logging import setup_logging
from backend.shared.middleware import RequestIdMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()

    try:
        await init_postgres(settings.postgres_url)
        await init_mongo(settings.mongo_url)
        await init_beanie_documents(
            [ConversationDocument, NutritionProfileDocument, DietPlanDocument, DietPlanExportDocument]
        )
        await init_llm_provider(settings)
    except Exception as e:
        logging.error(f"Failed to initialize databases: {e}")
        raise

    email_retry_task = asyncio.create_task(run_email_retry_loop(settings))

    yield

    email_retry_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await email_retry_task

    await close_postgres()
    await close_mongo()
    await close_llm_provider()


def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    # Added last so it wraps everything else (Starlette's middleware stack is
    # applied in reverse registration order) — CORS headers/preflight need to
    # be the outermost layer.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    Path(settings.dietitian_photos_storage_dir).mkdir(parents=True, exist_ok=True)
    app.mount(
        settings.dietitian_photos_base_url,
        StaticFiles(directory=settings.dietitian_photos_storage_dir),
        name="dietitian-photos",
    )

    @app.get(f"{settings.api_prefix}/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()