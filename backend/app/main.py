from fastapi import FastAPI

from backend.app.api_router import api_router
from backend.shared.config import get_settings
from backend.shared.exceptions import register_exception_handlers
from backend.shared.logging import setup_logging
from backend.shared.middleware import RequestIdMiddleware


def create_app() -> FastAPI:
    settings = get_settings()

    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
    )

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get(f"{settings.api_prefix}/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()