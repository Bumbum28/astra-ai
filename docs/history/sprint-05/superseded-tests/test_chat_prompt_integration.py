from collections.abc import AsyncIterator
from uuid import uuid4

import pytest

from app.core.config import AppConfig
from app.domains.characters.schemas import CharacterCreateRequest
from app.domains.characters.service import CharacterService
from app.domains.chat.service import ChatApplicationService
from app.domains.conversations.schemas import ConversationCreateRequest
from app.domains.conversations.service import ConversationService
from app.domains.messages.schemas import MessageSendRequest
from app.domains.personas.schemas import PersonaCreateRequest
from app.domains.personas.service import PersonaService
from app.domains.relationships.service import RelationshipService
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import LLMChunk, LLMRequest, LLMResponse
from app.tests.unit.fakes import FakeUnitOfWorkFactory


class RecordingLLMService(LLMChatService):
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(
            content="Kael đáp lại.",
            model=request.model or "roleplay-engine",
            provider=provider_name,
            finish_reason="stop",
        )

    def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_chat_composes_pinned_profiles_and_increments_turn_count() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        default_llm_provider="ollama",
        default_llm_model="roleplay-engine",
        intelligence_enabled=False,
    )
    user_id = uuid4()
    character = await CharacterService(uow_factory).create(
        user_id,
        CharacterCreateRequest(
            name="Kael",
            personality="Kiềm chế và bảo vệ.",
            speaking_style="Chậm rãi.",
        ),
    )
    persona = await PersonaService(uow_factory).create(
        user_id,
        PersonaCreateRequest(name="Ari", pronouns="hắn"),
    )
    conversation = await ConversationService(uow_factory, config).create(
        user_id,
        ConversationCreateRequest(
            character_id=character.id,
            persona_id=persona.id,
            system_prompt="Giữ nhịp kể chậm.",
        ),
    )
    llm = RecordingLLMService()

    await ChatApplicationService(uow_factory, llm, config).send_message(
        user_id,
        conversation.id,
        MessageSendRequest(content="Anh là ai?", client_message_id=uuid4()),
    )
    relationship = await RelationshipService(uow_factory).get(
        user_id,
        conversation.id,
    )

    assert len(llm.requests) == 1
    system_message = llm.requests[0].messages[0]
    assert "# Character profile" in system_message.content
    assert "Name: Kael" in system_message.content
    assert "# User persona" in system_message.content
    assert "Name used by the user: Ari" in system_message.content
    assert "# Relationship state" in system_message.content
    assert "Giữ nhịp kể chậm." in system_message.content
    assert relationship.turn_count == 1
