from typing import Annotated

from fastapi import Depends

from app.context.assembler import ContextAssembler, ConversationContextAssembler
from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory


def get_context_assembler(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> ContextAssembler:
    return ConversationContextAssembler(uow_factory, config)
