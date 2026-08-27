from typing import Annotated

from fastapi import Depends

from app.agents.policy import AgentPolicy
from app.agents.runtime import AgentRuntime
from app.agents.service import AgentChatService, AgentQueryService
from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.llm.chat.service import ChatService as LLMChatService
from app.llm.dependencies import get_llm_chat_service
from app.tools.dependencies import get_tool_executor, get_tool_registry
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


def get_agent_policy(
    config: Annotated[AppConfig, Depends(get_config)],
) -> AgentPolicy:
    return AgentPolicy(
        max_steps=config.agent_max_steps,
        max_tool_calls=config.agent_max_tool_calls,
        timeout_seconds=config.agent_timeout_seconds,
        default_allowed_tools=frozenset(config.agent_default_allowed_tools),
    )


def get_agent_runtime(
    llm_service: Annotated[LLMChatService, Depends(get_llm_chat_service)],
    registry: Annotated[ToolRegistry, Depends(get_tool_registry)],
    executor: Annotated[ToolExecutor, Depends(get_tool_executor)],
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    policy: Annotated[AgentPolicy, Depends(get_agent_policy)],
) -> AgentRuntime:
    return AgentRuntime(llm_service, registry, executor, uow_factory, policy)


def get_agent_chat_service(
    runtime: Annotated[AgentRuntime, Depends(get_agent_runtime)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> AgentChatService:
    return AgentChatService(runtime, config)


def get_agent_query_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> AgentQueryService:
    return AgentQueryService(uow_factory)
