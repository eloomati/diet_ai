from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .base import AppException
from .error_codes import ErrorCode
from .schemas import ErrorResponse, utc_now_z

_STATUS_TO_CODE: dict[int, ErrorCode] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHORIZED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    422: ErrorCode.VALIDATION_ERROR,
}


def _code_for_status(status_code: int) -> ErrorCode:
    if status_code >= 500:
        return ErrorCode.INTERNAL_ERROR
    return _STATUS_TO_CODE.get(status_code, ErrorCode.BAD_REQUEST)


def _error_payload(code: ErrorCode, message: str) -> dict:
    return ErrorResponse(code=code.value, message=message, timestamp=utc_now_z()).model_dump()


def _format_request_validation_message(exc: RequestValidationError) -> str:
    parts = []
    for error in exc.errors():
        loc = ".".join(str(segment) for segment in error["loc"] if segment != "body")
        parts.append(f"{loc}: {error['msg']}" if loc else error["msg"])
    return "; ".join(parts) or "Validation error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(_code_for_status(exc.status_code), str(exc.detail)),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_payload(ErrorCode.VALIDATION_ERROR, _format_request_validation_message(exc)),
        )

    @app.exception_handler(ValidationError)
    async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_payload(ErrorCode.VALIDATION_ERROR, str(exc)),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, __: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_payload(ErrorCode.INTERNAL_ERROR, "Internal server error"),
        )