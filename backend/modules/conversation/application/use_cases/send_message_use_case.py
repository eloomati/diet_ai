from backend.modules.ai.application.prompt_builder import PromptBuilder
from backend.modules.ai.domain import LLMProvider
from backend.modules.conversation.application.dto.send_message_dto import (
    SendMessageCommand,
    SendMessageResult,
)
from backend.modules.conversation.application.use_cases.exceptions import ConversationNotFoundError
from backend.modules.conversation.domain import ConversationRepository, MessageRole


class SendMessageUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        llm_provider: LLMProvider,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._llm_provider = llm_provider

    async def execute(self, command: SendMessageCommand) -> SendMessageResult:
        conversation = await self._conversation_repository.get_by_id(command.conversation_id)
        if conversation is None or conversation.user_id != command.user_id:
            raise ConversationNotFoundError("Conversation not found.")

        # Build the prompt from history *before* appending the new question,
        # so conversation_history doesn't duplicate the current question.
        prompt = PromptBuilder.build(conversation, question=command.content)

        user_message = conversation.add_message(role=MessageRole.USER, content=command.content)

        ai_response = await self._llm_provider.generate_response(prompt)

        assistant_message = conversation.add_message(
            role=MessageRole.ASSISTANT,
            content=ai_response.content,
            token_usage=ai_response.tokens,
        )

        await self._conversation_repository.save(conversation)

        return SendMessageResult(
            conversation_id=str(conversation.id),
            user_message_id=str(user_message.id),
            assistant_message_id=str(assistant_message.id),
            assistant_content=assistant_message.content,
        )
