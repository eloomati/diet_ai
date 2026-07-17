from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from backend.modules.nutrition.domain.exceptions.nutrition_domain_errors import (
    InvalidNutritionProfileError,
)
from backend.modules.nutrition.domain.value_objects.activity_level import ActivityLevel
from backend.modules.nutrition.domain.value_objects.diet_goal import DietGoal
from backend.modules.nutrition.domain.value_objects.diet_type import DietType

_MIN_AGE, _MAX_AGE = 1, 120
_MIN_HEIGHT_CM, _MAX_HEIGHT_CM = 50, 250
_MIN_WEIGHT_KG, _MAX_WEIGHT_KG = 20, 400


@dataclass(slots=True)
class NutritionProfile:
    id: UUID
    user_id: UUID
    age: int
    height_cm: int
    weight_kg: float
    activity_level: ActivityLevel
    goal: DietGoal
    diet_type: DietType
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        user_id: UUID,
        age: int,
        height_cm: int,
        weight_kg: float,
        activity_level: ActivityLevel,
        goal: DietGoal,
        diet_type: DietType,
    ) -> "NutritionProfile":
        cls._validate(age, height_cm, weight_kg)
        now = datetime.now(UTC)
        return cls(
            id=uuid4(),
            user_id=user_id,
            age=age,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal,
            diet_type=diet_type,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        age: int | None = None,
        height_cm: int | None = None,
        weight_kg: float | None = None,
        activity_level: ActivityLevel | None = None,
        goal: DietGoal | None = None,
        diet_type: DietType | None = None,
    ) -> None:
        new_age = age if age is not None else self.age
        new_height_cm = height_cm if height_cm is not None else self.height_cm
        new_weight_kg = weight_kg if weight_kg is not None else self.weight_kg
        self._validate(new_age, new_height_cm, new_weight_kg)

        self.age = new_age
        self.height_cm = new_height_cm
        self.weight_kg = new_weight_kg
        if activity_level is not None:
            self.activity_level = activity_level
        if goal is not None:
            self.goal = goal
        if diet_type is not None:
            self.diet_type = diet_type
        self.updated_at = datetime.now(UTC)

    def as_prompt_text(self) -> str:
        return (
            f"{self.age} years old, {self.height_cm}cm, {self.weight_kg}kg, "
            f"activity level: {self.activity_level.value}, "
            f"goal: {self.goal.value}, diet: {self.diet_type.value}"
        )

    @staticmethod
    def _validate(age: int, height_cm: int, weight_kg: float) -> None:
        if not (_MIN_AGE <= age <= _MAX_AGE):
            raise InvalidNutritionProfileError(f"Age must be between {_MIN_AGE} and {_MAX_AGE}.")
        if not (_MIN_HEIGHT_CM <= height_cm <= _MAX_HEIGHT_CM):
            raise InvalidNutritionProfileError(
                f"Height must be between {_MIN_HEIGHT_CM} and {_MAX_HEIGHT_CM} cm."
            )
        if not (_MIN_WEIGHT_KG <= weight_kg <= _MAX_WEIGHT_KG):
            raise InvalidNutritionProfileError(
                f"Weight must be between {_MIN_WEIGHT_KG} and {_MAX_WEIGHT_KG} kg."
            )
