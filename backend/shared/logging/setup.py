import logging
import sys

from .filters import RequestIdFilter


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Clear handlers to avoid duplicated logs on reload/tests.
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level.upper())
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [request_id=%(request_id)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)

    # Important: attach filter to handler so every emitted record gets request_id,
    # including third-party loggers like httpx/httpcore.
    handler.addFilter(RequestIdFilter())
    root.addHandler(handler)

    # Uvicorn configures "uvicorn"/"uvicorn.access" with their own handlers and
    # propagate=False (see uvicorn.config.LOGGING_CONFIG) — without this, their
    # formatter has no timestamp and they never reach our handler above, so
    # lines like "Waiting for application startup." print bare, undated.
    for logger_name in ("uvicorn", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True