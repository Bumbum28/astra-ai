from uuid import uuid4

import pytest

from app.core.config import AppConfig
from app.domains.conversations.schemas import (
    ConversationCreateRequest,
    ConversationUpdateRequest,
)
from app.domains.conversations.service import ConversationService
from app.tests.unit.fakes import FakeUnitOfWorkFactory


@pytest.mark.asyncio
async def test_conversation_service_creates_updates_and_archives_owned_record() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ConversationService(
        uow_factory,
        AppConfig(
            default_llm_provider="ollama",
            default_llm_model="roleplay-engine",
        ),
    )
    user_id = uuid4()

    created = await service.create(
        user_id,
        ConversationCreateRequest(title="  Cuộc trò chuyện mới  "),
    )
    updated = await service.update(
        user_id,
        created.id,
        ConversationUpdateRequest(title="Tên mới"),
    )
    page = await service.list_for_user(user_id, limit=30, cursor=None)
    await service.archive(user_id, created.id)
    archived_page = await service.list_for_user(user_id, limit=30, cursor=None)

    assert created.provider == "ollama"
    assert created.model == "roleplay-engine"
    assert updated.title == "Tên mới"
    assert len(page.items) == 1
    assert archived_page.items == []
