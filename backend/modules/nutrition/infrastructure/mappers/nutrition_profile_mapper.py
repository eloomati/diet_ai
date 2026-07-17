from backend.modules.nutrition.domain.entities.nutrition_profile import NutritionProfile
from backend.modules.nutrition.domain.value_objects.activity_level import ActivityLevel
from backend.modules.nutrition.domain.value_objects.diet_goal import DietGoal
from backend.modules.nutrition.domain.value_objects.diet_type import DietType
from backend.modules.nutrition.infrastructure.documents.nutrition_profile_document import (
    NutritionProfileDocument,
)


class NutritionProfileMapper:
    @staticmethod
    def to_domain(document: NutritionProfileDocument) -> NutritionProfile:
        return NutritionProfile(
            id=document.id,
            user_id=document.user_id,
            age=document.age,
            height_cm=document.height_cm,
            weight_kg=document.weight_kg,
            activity_level=ActivityLevel(document.activity_level),
            goal=DietGoal(document.goal),
            diet_type=DietType(document.diet_type),
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    @staticmethod
    def to_document(profile: NutritionProfile) -> NutritionProfileDocument:
        return NutritionProfileDocument(
            id=profile.id,
            user_id=profile.user_id,
            age=profile.age,
            height_cm=profile.height_cm,
            weight_kg=profile.weight_kg,
            activity_level=profile.activity_level.value,
            goal=profile.goal.value,
            diet_type=profile.diet_type.value,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
