import logging

from .context import request_id_ctx


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Always provide request_id so formatter never crashes.
        record.request_id = request_id_ctx.get("-")
        return True