from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    timestamp: str = Field(
        description="UTC timestamp in ISO8601 format with Z suffix"
    )


def utc_now_z() -> str:
    # Example: 2026-07-17T12:00:00Z
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")