from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Meal:
    name: str
    calories: float
    protein: float
    carbohydrates: float
    fat: float
