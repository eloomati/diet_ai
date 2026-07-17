import logging
import sys


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

    root.addHandler(handler)

    # Inject request_id from contextvar into every log record.
    from .filters import RequestIdFilter
    root.addFilter(RequestIdFilter())