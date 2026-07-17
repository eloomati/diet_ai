from uuid import UUID, uuid4

import pytest

from backend.modules.conversation.application import (
    CreateConversationCommand,
    CreateConversationUseCase,
)
from backend.modules.conversation.tests.fakes import InMemoryConversationRepository


@pytest.mark.asyncio
async def test_create_conversation_success() -> None:
    repo = InMemoryConversationRepository()
    use_case = CreateConversationUseCase(repo)

    result = await use_case.execute(
        CreateConversationCommand(
            user_id=uuid4(),
            title="Breakfast ideas",
            category="BREAKFAST",
        )
    )

    assert result.conversation_id is not None
    assert result.title == "Breakfast ideas"
    assert result.category == "BREAKFAST"
    assert result.status == "ACTIVE"


@pytest.mark.asyncio
async def test_create_conversation_persists_it() -> None:
    repo = InMemoryConversationRepository()
    use_case = CreateConversationUseCase(repo)

    result = await use_case.execute(
        CreateConversationCommand(user_id=uuid4(), title="Leg day", category="GYM")
    )

    stored = await repo.get_by_id(UUID(result.conversation_id))
    assert stored is not None
    assert stored.title == "Leg day"
