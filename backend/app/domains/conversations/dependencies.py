from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.conversations.service import ConversationService


def get_conversation_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> ConversationService:
    return ConversationService(uow_factory, config)
