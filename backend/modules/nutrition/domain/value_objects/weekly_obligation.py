from dataclasses import dataclass
from datetime import time

from backend.modules.nutrition.domain.exceptions.nutrition_domain_errors import (
    InvalidWeeklyObligationError,
)
from backend.modules.nutrition.domain.value_objects.day_of_week import DayOfWeek


@dataclass(frozen=True, slots=True)
class WeeklyObligation:
    day_of_week: DayOfWeek
    start_time: time
    end_time: time
    label: str

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise InvalidWeeklyObligationError("Obligation label cannot be empty.")
        if self.end_time <= self.start_time:
            raise InvalidWeeklyObligationError("Obligation end_time must be after start_time.")
