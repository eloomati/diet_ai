from backend.modules.dietitian.domain.entities.dietitian_application import DietitianApplication
from backend.modules.dietitian.domain.value_objects.application_status import ApplicationStatus
from backend.modules.dietitian.infrastructure.persistence.models.dietitian_application_model import (
    DietitianApplicationModel,
)


class DietitianApplicationMapper:
    @staticmethod
    def to_domain(model: DietitianApplicationModel) -> DietitianApplication:
        return DietitianApplication(
            id=model.id,
            user_id=model.user_id,
            experience=model.experience,
            diplomas=tuple(model.diplomas),
            description=model.description,
            status=ApplicationStatus(model.status),
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(application: DietitianApplication) -> DietitianApplicationModel:
        return DietitianApplicationModel(
            id=application.id,
            user_id=application.user_id,
            experience=application.experience,
            diplomas=list(application.diplomas),
            description=application.description,
            status=application.status.value,
            reviewed_by=application.reviewed_by,
            reviewed_at=application.reviewed_at,
            created_at=application.created_at,
            updated_at=application.updated_at,
        )
