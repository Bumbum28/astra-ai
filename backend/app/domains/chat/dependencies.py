from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.chat.service import ChatApplicationService
from app.domains.prompts.composer import StructuredPromptComposer
from app.domains.prompts.service import RoleplayPromptContextResolver
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.dependencies import get_llm_chat_service


def get_chat_application_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    llm_service: Annotated[LLMChatService, Depends(get_llm_chat_service)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> ChatApplicationService:
    return ChatApplicationService(
        uow_factory,
        llm_service,
        config,
        RoleplayPromptContextResolver(),
        StructuredPromptComposer(),
    )
