from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.rag.dependencies import get_rag_service
from app.rag.service import RAGService
from app.tools.builtins.search_conversation import SearchConversationTool
from app.tools.builtins.search_knowledge import SearchKnowledgeTool
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


def get_tool_registry(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    rag_service: Annotated[RAGService, Depends(get_rag_service)],
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        "search_knowledge",
        lambda: SearchKnowledgeTool(rag_service),
    )
    registry.register(
        "search_conversation",
        lambda: SearchConversationTool(uow_factory),
    )
    return registry


def get_tool_executor(
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> ToolExecutor:
    return ToolExecutor(registry, timeout_seconds=config.tool_execution_timeout_seconds)
