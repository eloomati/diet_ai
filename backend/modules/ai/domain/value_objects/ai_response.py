from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AIResponse:
    content: str
    model: str
    tokens: int
    execution_time: float
