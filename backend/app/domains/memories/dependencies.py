from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.memories.service import MemoryService
from app.embeddings.dependencies import get_embedding_service
from app.embeddings.service import EmbeddingService


def get_memory_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    embeddings: Annotated[EmbeddingService, Depends(get_embedding_service)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> MemoryService:
    return MemoryService(uow_factory, embeddings, config)
