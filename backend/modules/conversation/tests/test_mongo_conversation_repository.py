from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio

from backend.modules.conversation.domain import Conversation, ConversationCategory, MessageRole
from backend.modules.conversation.infrastructure.documents import ConversationDocument
from backend.modules.conversation.infrastructure.repository.mongo_conversation_repository import (
    MongoConversationRepository,
)
from backend.shared.config import get_settings
from backend.shared.database import close_mongo, init_beanie_documents, init_mongo


@pytest_asyncio.fixture
async def repository() -> AsyncGenerator[MongoConversationRepository, None]:
    # Beanie's client is bound to the event loop it's created in — init it here,
    # inside this test's own loop, instead of relying on the app's lifespan
    # (which runs in TestClient's separate portal loop/thread).
    settings = get_settings()
    await init_mongo(settings.mongo_url)
    await init_beanie_documents([ConversationDocument])
    yield MongoConversationRepository()
    await close_mongo()


@pytest.mark.asyncio
async def test_save_and_get_by_id_round_trips(repository: MongoConversationRepository) -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Breakfast ideas", category=ConversationCategory.BREAKFAST
    )
    conversation.add_message(role=MessageRole.USER, content="What should I eat?")

    await repository.save(conversation)
    fetched = await repository.get_by_id(conversation.id)

    assert fetched is not None
    assert fetched.id == conversation.id
    assert fetched.title == "Breakfast ideas"
    assert fetched.category == ConversationCategory.BREAKFAST
    assert len(fetched.messages) == 1
    assert fetched.messages[0].content == "What should I eat?"


@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_unknown_id(repository: MongoConversationRepository) -> None:
    assert await repository.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_save_upserts_existing_conversation(repository: MongoConversationRepository) -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="Leg day", category=ConversationCategory.GYM
    )
    await repository.save(conversation)

    conversation.add_message(role=MessageRole.USER, content="Squats today?")
    await repository.save(conversation)

    fetched = await repository.get_by_id(conversation.id)
    assert len(fetched.messages) == 1


@pytest.mark.asyncio
async def test_list_by_user_returns_only_own_conversations(repository: MongoConversationRepository) -> None:
    user_id = uuid4()

    await repository.save(
        Conversation.create(user_id=user_id, title="Breakfast ideas", category=ConversationCategory.BREAKFAST)
    )
    await repository.save(
        Conversation.create(user_id=user_id, title="Leg day", category=ConversationCategory.GYM)
    )
    await repository.save(
        Conversation.create(user_id=uuid4(), title="Someone else's chat", category=ConversationCategory.GENERAL)
    )

    conversations = await repository.list_by_user(user_id)

    assert {c.title for c in conversations} == {"Breakfast ideas", "Leg day"}


@pytest.mark.asyncio
async def test_delete_removes_conversation(repository: MongoConversationRepository) -> None:
    conversation = Conversation.create(
        user_id=uuid4(), title="To delete", category=ConversationCategory.GENERAL
    )
    await repository.save(conversation)

    await repository.delete(conversation.id)

    assert await repository.get_by_id(conversation.id) is None


@pytest.mark.asyncio
async def test_delete_unknown_id_is_a_no_op(repository: MongoConversationRepository) -> None:
    await repository.delete(uuid4())


@pytest.mark.asyncio
async def test_user_id_index_is_created(repository: MongoConversationRepository) -> None:
    collection = ConversationDocument.get_pymongo_collection()

    index_info = await collection.index_information()

    assert any(("user_id", 1) in spec["key"] for spec in index_info.values())
