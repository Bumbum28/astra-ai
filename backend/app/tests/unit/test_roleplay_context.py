from uuid import uuid4

import pytest

from app.context.assembler import ConversationContextAssembler
from app.context.contracts import ContextAssemblyRequest
from app.core.config import AppConfig
from app.domains.characters.schemas import CharacterCreateRequest
from app.domains.characters.service import CharacterService
from app.domains.conversations.schemas import ConversationCreateRequest
from app.domains.conversations.service import ConversationService
from app.domains.memories.model import MemoryKind, MemoryScope
from app.domains.memories.schemas import MemoryCreateRequest
from app.domains.memories.service import MemoryService
from app.domains.messages.model import Message, MessageContentType, MessageRole, MessageStatus
from app.domains.personas.schemas import PersonaCreateRequest
from app.domains.personas.service import PersonaService
from app.tests.unit.fakes import FakeUnitOfWorkFactory


@pytest.mark.asyncio
async def test_context_assembler_composes_character_persona_and_memory() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        platform_system_prompt="Platform rules",
        memory_context_limit=10,
        memory_min_importance=0.0,
    )
    user_id = uuid4()
    character = await CharacterService(uow_factory).create(
        user_id,
        CharacterCreateRequest(
            name="Elara",
            personality="Calm and observant",
            system_prompt="Stay in character.",
        ),
    )
    persona = await PersonaService(uow_factory).create(
        user_id,
        PersonaCreateRequest(
            name="Traveler",
            description="A cautious explorer",
            is_default=True,
        ),
    )
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(
            character_id=character.id,
            persona_id=persona.id,
        ),
    )
    await MemoryService(uow_factory).create(
        user_id,
        MemoryCreateRequest(
            scope=MemoryScope.CHARACTER,
            kind=MemoryKind.RELATIONSHIP,
            content="Elara trusts the traveler after the bridge incident.",
            importance=0.9,
            character_id=character.id,
        ),
    )
    history = [
        Message(
            id=uuid4(),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Do you remember me?",
            content_type=MessageContentType.MARKDOWN,
            status=MessageStatus.COMPLETED,
            message_metadata={},
        )
    ]
    conversation_model = uow_factory.conversations.items[conversation.id]
    assembled = await ConversationContextAssembler(uow_factory, config).assemble(
        ContextAssemblyRequest(
            user_id=user_id,
            conversation=conversation_model,
            history=history,
        )
    )

    assert assembled.character_id == character.id
    assert assembled.persona_id == persona.id
    assert len(assembled.memory_ids) == 1
    assert assembled.messages[0].role.value == "system"
    system_prompt = assembled.messages[0].content
    assert "Elara" in system_prompt
    assert "Traveler" in system_prompt
    assert "bridge incident" in system_prompt
    assert assembled.messages[-1].content == "Do you remember me?"


@pytest.mark.asyncio
async def test_conversation_rejects_foreign_character_reference() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(default_llm_provider="ollama", default_llm_model="roleplay-engine")
    owner_id = uuid4()
    other_user_id = uuid4()
    character = await CharacterService(uow_factory).create(
        owner_id,
        CharacterCreateRequest(name="Private character"),
    )

    with pytest.raises(Exception):
        await ConversationService(uow_factory, config).create(
            other_user_id,
            ConversationCreateRequest(character_id=character.id),
        )
