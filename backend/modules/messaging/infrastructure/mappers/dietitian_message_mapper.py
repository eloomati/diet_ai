from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender
from backend.modules.messaging.infrastructure.persistence.models.dietitian_message_model import (
    DietitianMessageModel,
)


class DietitianMessageMapper:
    @staticmethod
    def to_domain(model: DietitianMessageModel) -> DietitianMessage:
        return DietitianMessage(
            id=model.id,
            thread_id=model.thread_id,
            sender=MessageSender(model.sender),
            content=model.content,
            diet_plan_id=model.diet_plan_id,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(message: DietitianMessage) -> DietitianMessageModel:
        return DietitianMessageModel(
            id=message.id,
            thread_id=message.thread_id,
            sender=message.sender.value,
            content=message.content,
            diet_plan_id=message.diet_plan_id,
            created_at=message.created_at,
        )
