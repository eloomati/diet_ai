from pydantic import BaseModel, Field

from backend.modules.conversation.domain import ConversationCategory


class CreateConversationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    categories: list[ConversationCategory] = Field(min_length=1)


class CreateConversationResponse(BaseModel):
    conversation_id: str
    title: str
    categories: list[str]
    status: str


class ConversationSummaryResponse(BaseModel):
    conversation_id: str
    title: str
    categories: list[str]
    status: str
    updated_at: str


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    title: str
    categories: list[str]
    status: str
    messages: list[MessageResponse]


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class SendMessageResponse(BaseModel):
    conversation_id: str
    user_message_id: str
    assistant_message_id: str
    assistant_content: str
