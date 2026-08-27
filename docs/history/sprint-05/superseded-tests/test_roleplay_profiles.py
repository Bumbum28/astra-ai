from uuid import uuid4

import pytest

from app.core.config import AppConfig
from app.domains.characters.schemas import (
    CharacterCreateRequest,
    CharacterUpdateRequest,
)
from app.domains.characters.service import CharacterService
from app.domains.conversations.schemas import ConversationCreateRequest
from app.domains.conversations.service import ConversationService
from app.domains.personas.schemas import PersonaCreateRequest, PersonaUpdateRequest
from app.domains.personas.service import PersonaService
from app.domains.relationships.schemas import RelationshipUpdateRequest
from app.domains.relationships.service import RelationshipService
from app.tests.unit.fakes import FakeUnitOfWorkFactory


@pytest.mark.asyncio
async def test_character_and_persona_updates_create_new_versions() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    character_service = CharacterService(uow_factory)
    persona_service = PersonaService(uow_factory)

    character = await character_service.create(
        user_id,
        CharacterCreateRequest(
            name="Kael",
            personality="Lạnh lùng nhưng bảo vệ người dùng.",
        ),
    )
    updated_character = await character_service.update(
        user_id,
        character.id,
        CharacterUpdateRequest(speaking_style="Ngắn gọn và chậm rãi."),
    )
    persona = await persona_service.create(
        user_id,
        PersonaCreateRequest(name="Ari", pronouns="hắn"),
    )
    updated_persona = await persona_service.update(
        user_id,
        persona.id,
        PersonaUpdateRequest(background="Người sống sót từ khu phía bắc."),
    )

    assert updated_character.current_version == 2
    assert updated_character.personality == character.personality
    assert updated_character.speaking_style == "Ngắn gọn và chậm rãi."
    assert len(uow_factory.character_versions.items) == 2
    assert updated_persona.current_version == 2
    assert updated_persona.pronouns == "hắn"
    assert len(uow_factory.persona_versions.items) == 2


@pytest.mark.asyncio
async def test_conversation_pins_profile_versions_and_creates_relationship() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    character = await CharacterService(uow_factory).create(
        user_id,
        CharacterCreateRequest(
            name="Kael",
            provider="ollama",
            model="roleplay-engine",
            temperature=0.7,
        ),
    )
    persona = await PersonaService(uow_factory).create(
        user_id,
        PersonaCreateRequest(name="Ari"),
    )
    service = ConversationService(
        uow_factory,
        AppConfig(
            default_llm_provider="openai",
            default_llm_model="gpt-4.1-mini",
        ),
    )

    conversation = await service.create(
        user_id,
        ConversationCreateRequest(
            character_id=character.id,
            persona_id=persona.id,
        ),
    )
    relationship = await RelationshipService(uow_factory).get(
        user_id,
        conversation.id,
    )

    assert conversation.character_id == character.id
    assert conversation.character_version_id is not None
    assert conversation.persona_id == persona.id
    assert conversation.persona_version_id is not None
    assert conversation.provider == "ollama"
    assert conversation.model == "roleplay-engine"
    assert conversation.temperature == 0.7
    assert relationship.level.value == "l0"
    assert relationship.affection_score == 0


@pytest.mark.asyncio
async def test_relationship_update_records_auditable_event() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    user_id = uuid4()
    character = await CharacterService(uow_factory).create(
        user_id,
        CharacterCreateRequest(name="Kael"),
    )
    conversation = await ConversationService(
        uow_factory,
        AppConfig(
            default_llm_provider="ollama",
            default_llm_model="roleplay-engine",
        ),
    ).create(
        user_id,
        ConversationCreateRequest(character_id=character.id),
    )
    service = RelationshipService(uow_factory)

    updated = await service.update(
        user_id,
        conversation.id,
        RelationshipUpdateRequest(
            level="l3",
            affection_score=42,
            status="Mập mờ",
            reason="Hai nhân vật bắt đầu tin tưởng nhau.",
        ),
    )
    history = await service.history(user_id, conversation.id, limit=50)

    assert updated.level.value == "l3"
    assert updated.affection_score == 42
    assert len(history.items) == 1
    assert history.items[0].previous_score == 0
    assert history.items[0].new_score == 42
    assert history.items[0].score_delta == 42
