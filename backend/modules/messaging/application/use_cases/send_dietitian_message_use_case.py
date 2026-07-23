from backend.modules.messaging.application.dto.messaging_dto import (
    DietitianMessageResult,
    SendMessageCommand,
)
from backend.modules.messaging.application.use_cases.exceptions import (
    ThreadAccessDeniedError,
    ThreadNotFoundError,
)
from backend.modules.messaging.domain.entities.dietitian_message import DietitianMessage
from backend.modules.messaging.domain.repositories.dietitian_message_repository import (
    DietitianMessageRepository,
)
from backend.modules.messaging.domain.repositories.dietitian_thread_repository import (
    DietitianThreadRepository,
)
from backend.modules.messaging.domain.value_objects.message_sender import MessageSender
from backend.modules.notifications.application.use_cases.create_notification_use_case import (
    CreateNotificationUseCase,
)
from backend.modules.notifications.domain.value_objects.notification_type import (
    NotificationType,
)


class SendDietitianMessageUseCase:
    def __init__(
        self,
        thread_repository: DietitianThreadRepository,
        message_repository: DietitianMessageRepository,
        create_notification_use_case: CreateNotificationUseCase,
    ) -> None:
        self._thread_repository = thread_repository
        self._message_repository = message_repository
        self._create_notification_use_case = create_notification_use_case

    async def execute(self, command: SendMessageCommand) -> DietitianMessageResult:
        thread = await self._thread_repository.get_by_id(command.thread_id)
        if thread is None:
            raise ThreadNotFoundError("Thread not found.")

        # `sender` is derived from which participant the caller is — never
        # accepted from the client.
        if command.caller_id == thread.user_id:
            sender = MessageSender.USER
        elif command.caller_id == thread.dietitian_id:
            sender = MessageSender.DIETITIAN
        else:
            raise ThreadAccessDeniedError("You are not a participant of this thread.")

        message = DietitianMessage.create(
            thread_id=thread.id,
            sender=sender,
            content=command.content,
            diet_plan_id=command.diet_plan_id,
        )
        await self._message_repository.save(message)

        # Direct, synchronous call — not a second Kafka round-trip. Kafka
        # is for cross-cutting distribution of an event a whole different
        # module reacts to independently (TransactionPaid); a message
        # being sent and its recipient being notified happen in the same
        # request, same module boundary `messaging` already crosses.
        await self._create_notification_use_case.execute(
            recipient_user_id=thread.other_participant(command.caller_id),
            type=NotificationType.NEW_MESSAGE,
            reference_id=thread.id,
        )

        return DietitianMessageResult.from_domain(message)
