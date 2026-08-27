from typing import Annotated

from fastapi import Depends

from app.agents.dependencies import get_agent_chat_service
from app.agents.service import AgentChatService
from app.context.assembler import ContextAssembler
from app.context.dependencies import get_context_assembler
from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.chat.orchestrator import ChatOrchestrator
from app.domains.chat.service import ChatApplicationService
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.dependencies import get_llm_chat_service


def get_chat_application_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    llm_service: Annotated[LLMChatService, Depends(get_llm_chat_service)],
    config: Annotated[AppConfig, Depends(get_config)],
    context_assembler: Annotated[ContextAssembler, Depends(get_context_assembler)],
) -> ChatApplicationService:
    """Return the direct-chat execution path for backwards-compatible tests/use."""
    return ChatApplicationService(uow_factory, llm_service, config, context_assembler)


def get_agent_chat_application_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    agent_service: Annotated[AgentChatService, Depends(get_agent_chat_service)],
    config: Annotated[AppConfig, Depends(get_config)],
    context_assembler: Annotated[ContextAssembler, Depends(get_context_assembler)],
) -> ChatApplicationService:
    return ChatApplicationService(uow_factory, agent_service, config, context_assembler)


def get_chat_orchestrator(
    direct_service: Annotated[
        ChatApplicationService,
        Depends(get_chat_application_service),
    ],
    agent_service: Annotated[
        ChatApplicationService,
        Depends(get_agent_chat_application_service),
    ],
) -> ChatOrchestrator:
    return ChatOrchestrator(direct_service, agent_service)
