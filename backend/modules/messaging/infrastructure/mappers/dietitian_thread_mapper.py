from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread
from backend.modules.messaging.infrastructure.persistence.models.dietitian_thread_model import (
    DietitianThreadModel,
)


class DietitianThreadMapper:
    @staticmethod
    def to_domain(model: DietitianThreadModel) -> DietitianThread:
        return DietitianThread(
            id=model.id,
            user_id=model.user_id,
            dietitian_id=model.dietitian_id,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(thread: DietitianThread) -> DietitianThreadModel:
        return DietitianThreadModel(
            id=thread.id,
            user_id=thread.user_id,
            dietitian_id=thread.dietitian_id,
            created_at=thread.created_at,
        )
