from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.knowledge.service import KnowledgeService
from app.rag.dependencies import get_rag_service
from app.rag.service import RAGService


def get_knowledge_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> KnowledgeService:
    return KnowledgeService(uow_factory, rag_service, config)
