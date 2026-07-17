from datetime import datetime
from uuid import UUID, uuid4

from beanie import Document
from pydantic import BaseModel, Field


class MessageEmbedded(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    token_usage: int | None = None


class ConversationDocument(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    title: str
    category: str
    status: str
    messages: list[MessageEmbedded] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Settings:
        name = "conversations"
