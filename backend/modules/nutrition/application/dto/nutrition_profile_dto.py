from dataclasses import dataclass
from datetime import time
from uuid import UUID

from backend.modules.nutrition.domain.entities.nutrition_profile import NutritionProfile
from backend.modules.nutrition.domain.value_objects.day_of_week import DayOfWeek
from backend.modules.nutrition.domain.value_objects.weekly_obligation import WeeklyObligation


@dataclass(frozen=True, slots=True)
class WeeklyObligationInput:
    day_of_week: str
    start_time: str
    end_time: str
    label: str

    def to_domain(self) -> WeeklyObligation:
        return WeeklyObligation(
            day_of_week=DayOfWeek(self.day_of_week),
            start_time=time.fromisoformat(self.start_time),
            end_time=time.fromisoformat(self.end_time),
            label=self.label,
        )


@dataclass(frozen=True, slots=True)
class WeeklyObligationResult:
    day_of_week: str
    start_time: str
    end_time: str
    label: str

    @classmethod
    def from_domain(cls, obligation: WeeklyObligation) -> "WeeklyObligationResult":
        return cls(
            day_of_week=obligation.day_of_week.value,
            start_time=obligation.start_time.isoformat(timespec="minutes"),
            end_time=obligation.end_time.isoformat(timespec="minutes"),
            label=obligation.label,
        )


@dataclass(frozen=True, slots=True)
class CreateNutritionProfileCommand:
    user_id: UUID
    age: int
    height_cm: int
    weight_kg: float
    activity_level: str
    goal: str
    diet_type: str
    weekly_obligations: tuple[WeeklyObligationInput, ...] = ()


@dataclass(frozen=True, slots=True)
class UpdateNutritionProfileCommand:
    user_id: UUID
    age: int | None = None
    height_cm: int | None = None
    weight_kg: float | None = None
    activity_level: str | None = None
    goal: str | None = None
    diet_type: str | None = None
    weekly_obligations: tuple[WeeklyObligationInput, ...] | None = None


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
    weekly_obligations: tuple[WeeklyObligationResult, ...]
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
            weekly_obligations=tuple(
                WeeklyObligationResult.from_domain(o) for o in profile.weekly_obligations
            ),
            created_at=profile.created_at.isoformat(),
            updated_at=profile.updated_at.isoformat(),
        )
