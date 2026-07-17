from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.shared.logging.context import request_id_ctx


class RequestIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.header_name) or str(uuid4())
        token = request_id_ctx.set(request_id)
        try:
            response: Response = await call_next(request)
            response.headers[self.header_name] = request_id
            return response
        finally:
            request_id_ctx.reset(token)