from backend.modules.ai.application.prompt_builder import PromptBuilder
from backend.modules.ai.domain import LLMProvider
from backend.modules.conversation.application.dto.send_message_dto import (
    SendMessageCommand,
    SendMessageResult,
)
from backend.modules.conversation.application.use_cases.exceptions import ConversationNotFoundError
from backend.modules.conversation.domain import ConversationRepository, MessageRole
from backend.modules.nutrition.domain import NutritionProfileRepository


class SendMessageUseCase:
    def __init__(
        self,
        conversation_repository: ConversationRepository,
        llm_provider: LLMProvider,
        nutrition_profile_repository: NutritionProfileRepository,
    ) -> None:
        self._conversation_repository = conversation_repository
        self._llm_provider = llm_provider
        self._nutrition_profile_repository = nutrition_profile_repository

    async def execute(self, command: SendMessageCommand) -> SendMessageResult:
        conversation = await self._conversation_repository.get_by_id(command.conversation_id)
        if conversation is None or conversation.user_id != command.user_id:
            raise ConversationNotFoundError("Conversation not found.")

        profile = await self._nutrition_profile_repository.get_by_user_id(command.user_id)
        user_profile_text = profile.as_prompt_text() if profile else None

        # Build the prompt from history *before* appending the new question,
        # so conversation_history doesn't duplicate the current question.
        prompt = PromptBuilder.build(conversation, question=command.content, user_profile=user_profile_text)

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
