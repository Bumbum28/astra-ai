from typing import Annotated

from fastapi import Depends

from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.rag.postgres import PostgresKeywordRetriever
from app.rag.retriever import Retriever
from app.rag.service import RAGService


def get_retriever(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> Retriever:
    return PostgresKeywordRetriever(uow_factory)


def get_rag_service(
    retriever: Annotated[Retriever, Depends(get_retriever)],
) -> RAGService:
    return RAGService(retriever)
