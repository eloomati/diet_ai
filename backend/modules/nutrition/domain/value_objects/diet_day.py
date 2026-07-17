from dataclasses import dataclass

from backend.modules.nutrition.domain.value_objects.meal import Meal


@dataclass(frozen=True, slots=True)
class DietDay:
    day_number: int
    meals: tuple[Meal, ...]
