from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType
from backend.modules.notifications.infrastructure.persistence.models.notification_model import (
    NotificationModel,
)


class NotificationMapper:
    @staticmethod
    def to_domain(model: NotificationModel) -> Notification:
        return Notification(
            id=model.id,
            recipient_user_id=model.recipient_user_id,
            type=NotificationType(model.type),
            reference_id=model.reference_id,
            created_at=model.created_at,
            read_at=model.read_at,
        )

    @staticmethod
    def to_model(notification: Notification) -> NotificationModel:
        return NotificationModel(
            id=notification.id,
            recipient_user_id=notification.recipient_user_id,
            type=notification.type.value,
            reference_id=notification.reference_id,
            created_at=notification.created_at,
            read_at=notification.read_at,
        )
