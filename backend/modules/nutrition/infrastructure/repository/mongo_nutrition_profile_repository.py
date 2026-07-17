from uuid import UUID

from backend.modules.nutrition.domain.entities.nutrition_profile import NutritionProfile
from backend.modules.nutrition.domain.repositories.nutrition_profile_repository import (
    NutritionProfileRepository,
)
from backend.modules.nutrition.infrastructure.documents.nutrition_profile_document import (
    NutritionProfileDocument,
)
from backend.modules.nutrition.infrastructure.mappers.nutrition_profile_mapper import (
    NutritionProfileMapper,
)


class MongoNutritionProfileRepository(NutritionProfileRepository):
    async def get_by_user_id(self, user_id: UUID) -> NutritionProfile | None:
        document = await NutritionProfileDocument.find_one(NutritionProfileDocument.user_id == user_id)
        return NutritionProfileMapper.to_domain(document) if document else None

    async def save(self, profile: NutritionProfile) -> None:
        document = NutritionProfileMapper.to_document(profile)
        await document.save()
