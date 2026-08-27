from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

import pytest

from app.agents.policy import AgentPolicy
from app.agents.runtime import AgentRuntime
from app.agents.service import AgentChatService
from app.common.exceptions import AppException
from app.core.config import AppConfig
from app.llm.contracts import (
    LLMChunk,
    LLMMessage,
    LLMMessageRole,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)
from app.tests.unit.fakes import FakeUnitOfWorkFactory
from app.tools.base import BaseTool
from app.tools.contracts import ToolContext, ToolDefinition, ToolExecutionResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


class LookupTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="lookup",
            description="Look up a value for the agent.",
            input_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        )

    async def execute(
        self,
        arguments: dict[str, Any],
        context: ToolContext,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="lookup",
            content=f"stored-result:{arguments['query']}",
            data={"conversation_id": str(context.conversation_id)},
        )


class ScriptedLLMService:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    async def generate(self, provider_name: str, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if len(self.requests) == 1:
            return LLMResponse(
                content="",
                model=request.model or "test-model",
                provider=provider_name,
                tool_calls=[
                    LLMToolCall(
                        id="call-1",
                        name="lookup",
                        arguments={"query": "Astra Harbor"},
                    )
                ],
                usage=LLMUsage(
                    input_tokens=10,
                    output_tokens=1,
                    total_tokens=11,
                ),
            )
        assert request.messages[-1].role == LLMMessageRole.TOOL
        assert "stored-result:Astra Harbor" in request.messages[-1].content
        return LLMResponse(
            content="Đã tìm thấy Astra Harbor.",
            model=request.model or "test-model",
            provider=provider_name,
            finish_reason="stop",
            usage=LLMUsage(
                input_tokens=20,
                output_tokens=2,
                total_tokens=22,
            ),
        )

    def stream(
        self, provider_name: str, request: LLMRequest
    ) -> AsyncIterator[LLMChunk]:
        raise NotImplementedError


@pytest.mark.asyncio
async def test_agent_runtime_executes_tool_loop_and_persists_trace() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    llm = ScriptedLLMService()
    registry = ToolRegistry()
    registry.register("lookup", LookupTool)
    runtime = AgentRuntime(
        llm,  # type: ignore[arg-type]
        registry,
        ToolExecutor(registry, timeout_seconds=1),
        uow_factory,
        AgentPolicy(
            max_steps=4,
            max_tool_calls=4,
            timeout_seconds=5,
            default_allowed_tools=frozenset({"lookup"}),
        ),
    )
    user_id = uuid4()
    conversation_id = uuid4()

    response = await runtime.run(
        "ollama",
        LLMRequest(
            messages=[
                LLMMessage(role=LLMMessageRole.USER, content="Tìm Astra Harbor")
            ],
            model="roleplay-engine",
            metadata={
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "user_message_id": str(uuid4()),
                "assistant_message_id": str(uuid4()),
            },
        ),
    )

    assert response.content == "Đã tìm thấy Astra Harbor."
    assert response.metadata["execution_mode"] == "agent"
    assert response.metadata["agent_tool_call_count"] == 1
    assert response.usage == LLMUsage(
        input_tokens=30,
        output_tokens=3,
        total_tokens=33,
    )
    assert len(uow_factory.agents.runs) == 1
    run = next(iter(uow_factory.agents.runs.values()))
    assert run.status == "completed"
    assert run.tool_call_count == 1
    steps = await uow_factory.agents.list_steps(run.id)
    assert [step.kind for step in steps] == ["model", "tool", "model"]
    assert all(step.status == "completed" for step in steps)
    model_steps = [step for step in steps if step.kind == "model"]
    assert all("content_preview" not in step.output_payload for step in model_steps)
    assert [step.output_payload["content_chars"] for step in model_steps] == [0, 25]


@pytest.mark.asyncio
async def test_agent_chat_stream_carries_run_metadata_on_final_chunk() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    llm = ScriptedLLMService()
    registry = ToolRegistry()
    registry.register("lookup", LookupTool)
    runtime = AgentRuntime(
        llm,  # type: ignore[arg-type]
        registry,
        ToolExecutor(registry, timeout_seconds=1),
        uow_factory,
        AgentPolicy(
            max_steps=4,
            max_tool_calls=4,
            timeout_seconds=5,
            default_allowed_tools=frozenset({"lookup"}),
        ),
    )
    service = AgentChatService(runtime, AppConfig(agent_stream_chunk_chars=16))
    request = LLMRequest(
        messages=[LLMMessage(role=LLMMessageRole.USER, content="Tìm dữ liệu")],
        metadata={
            "user_id": str(uuid4()),
            "conversation_id": str(uuid4()),
        },
    )

    chunks = [chunk async for chunk in service.stream("ollama", request)]

    assert (
        "".join(chunk.content for chunk in chunks) == "Đã tìm thấy Astra Harbor."
    )
    assert chunks[-1].metadata["execution_mode"] == "agent"
    assert chunks[-1].metadata["agent_tool_call_count"] == 1
    assert chunks[-1].usage == LLMUsage(
        input_tokens=30,
        output_tokens=3,
        total_tokens=33,
    )


def test_agent_policy_rejects_tools_outside_configured_allowlist() -> None:
    registry = ToolRegistry()
    registry.register("lookup", LookupTool)
    registry.register("other", LookupTool)
    policy = AgentPolicy(
        max_steps=4,
        max_tool_calls=4,
        timeout_seconds=5,
        default_allowed_tools=frozenset({"lookup"}),
    )

    with pytest.raises(AppException) as caught:
        policy.resolve_allowed_tools(registry, ["other"])

    assert caught.value.code.value == "AGENT_INVALID_TOOL"
