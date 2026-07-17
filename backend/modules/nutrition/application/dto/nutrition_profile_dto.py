from dataclasses import dataclass
from uuid import UUID

from backend.modules.nutrition.domain.entities.nutrition_profile import NutritionProfile


@dataclass(frozen=True, slots=True)
class CreateNutritionProfileCommand:
    user_id: UUID
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str


@dataclass(frozen=True, slots=True)
class UpdateNutritionProfileCommand:
    user_id: UUID
    age: int | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    diet_type: str | None = None


@dataclass(frozen=True, slots=True)
class GetNutritionProfileQuery:
    user_id: UUID


@dataclass(frozen=True, slots=True)
class NutritionProfileResult:
    profile_id: str
    user_id: str
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str
    created_at: str
    updated_at: str

    @classmethod
    def from_domain(cls, profile: NutritionProfile) -> "NutritionProfileResult":
        return cls(
            profile_id=str(profile.id),
            user_id=str(profile.user_id),
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level.value,
            goal=profile.goal.value,
            diet_type=profile.diet_type.value,
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
        )
