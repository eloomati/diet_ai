import uuid

from backend.modules.notifications.domain.entities.notification import Notification
from backend.modules.notifications.domain.value_objects.notification_type import NotificationType


def test_create_sets_fields_and_defaults_unread() -> None:
    recipient_id = uuid.uuid4()
    reference_id = uuid.uuid4()

    notification = Notification.create(
        recipient_user_id=recipient_id,
        type=NotificationType.TRANSACTION_PAID,
        reference_id=reference_id,
    )

    assert notification.recipient_user_id == recipient_id
    assert notification.type == NotificationType.TRANSACTION_PAID
    assert notification.reference_id == reference_id
    assert notification.read_at is None


def test_mark_read_sets_read_at() -> None:
    notification = Notification.create(
        recipient_user_id=uuid.uuid4(),
        type=NotificationType.TRANSACTION_PAID,
        reference_id=uuid.uuid4(),
    )

    notification.mark_read()

    assert notification.read_at is not None


def test_mark_read_is_idempotent() -> None:
    notification = Notification.create(
        recipient_user_id=uuid.uuid4(),
        type=NotificationType.TRANSACTION_PAID,
        reference_id=uuid.uuid4(),
    )

    notification.mark_read()
    first_read_at = notification.read_at
    notification.mark_read()

    assert notification.read_at is not None
    assert notification.read_at >= first_read_at
