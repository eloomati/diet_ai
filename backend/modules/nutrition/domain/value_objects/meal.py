import datetime
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Meal:
    name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
    # Qualified `datetime.time`, not `from datetime import time`: a class-body
    # annotated assignment binds the value to the field name *before* evaluating
    # the annotation, so a field literally named `time` with a bare `time`
    # annotation would resolve to the value just assigned (None), not the type.
    time: datetime.time | None = None
