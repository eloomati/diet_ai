from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.dietitian.infrastructure.persistence.models.dietitian_profile_model import (
    DietitianProfileModel,
)


class DietitianProfileMapper:
    @staticmethod
    def to_domain(model: DietitianProfileModel) -> DietitianProfile:
        return DietitianProfile(
            id=model.id,
            user_id=model.user_id,
            experience=model.experience,
            diplomas=tuple(model.diplomas),
            description=model.description,
            photos=tuple(model.photos),
            first_name=model.first_name,
            last_name=model.last_name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(profile: DietitianProfile) -> DietitianProfileModel:
        return DietitianProfileModel(
            id=profile.id,
            user_id=profile.user_id,
            experience=profile.experience,
            diplomas=list(profile.diplomas),
            description=profile.description,
            photos=list(profile.photos),
            first_name=profile.first_name,
            last_name=profile.last_name,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
