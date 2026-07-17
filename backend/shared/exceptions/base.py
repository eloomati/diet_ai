from dataclasses import dataclass

from .error_codes import ErrorCode


@dataclass(slots=True)
class AppException(Exception):
    code: ErrorCode
    message: str
    status_code: int = 400

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"