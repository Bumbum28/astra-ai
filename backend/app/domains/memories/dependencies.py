from typing import Annotated

from fastapi import Depends

from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.memories.service import MemoryService


def get_memory_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> MemoryService:
    return MemoryService(uow_factory)
