from typing import Any
from uuid import uuid4

import pytest

from app.core.config import AppConfig
from app.domains.knowledge.chunker import chunk_text
from app.domains.knowledge.schemas import KnowledgeSearchRequest, KnowledgeSourceCreateRequest
from app.domains.knowledge.service import KnowledgeService
from app.rag.postgres import PostgresKeywordRetriever
from app.rag.service import RAGService
from app.tests.unit.fakes import FakeUnitOfWorkFactory
from app.tools.base import BaseTool
from app.tools.contracts import ToolContext, ToolDefinition, ToolExecutionResult
from app.tools.executor import ToolExecutor
from app.tools.registry import ToolRegistry


def test_chunk_text_is_deterministic_and_overlapping() -> None:
    text = " ".join(f"word{i}" for i in range(200))
    first = chunk_text(text, size=120, overlap=20)
    second = chunk_text(text, size=120, overlap=20)

    assert first == second
    assert len(first) > 1
    assert all(item.content for item in first)


@pytest.mark.asyncio
async def test_knowledge_service_persists_and_retrieves_owned_chunks() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    config = AppConfig(
        rag_chunk_size_chars=256,
        rag_chunk_overlap_chars=16,
    )
    rag = RAGService(PostgresKeywordRetriever(uow_factory))
    service = KnowledgeService(uow_factory, rag, config)
    user_id = uuid4()

    source = await service.create_source(
        user_id,
        KnowledgeSourceCreateRequest(
            name="World lore",
            content="The silver bridge leads to Astra Harbor. " * 12,
        ),
    )
    result = await service.search(
        user_id,
        KnowledgeSearchRequest(query="silver bridge", top_k=3),
    )

    assert source.name == "World lore"
    assert result.items
    assert all(item.source_id == source.id for item in result.items)
    assert "silver bridge" in result.items[0].content.lower()


class EchoTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="echo",
            description="Echo a value.",
            input_schema={"type": "object"},
        )

    async def execute(
        self, arguments: dict[str, Any], context: ToolContext
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name="echo",
            content=str(arguments.get("value") or ""),
            data={"user_id": str(context.user_id)},
        )


@pytest.mark.asyncio
async def test_tool_registry_and_executor_enforce_allow_list() -> None:
    registry = ToolRegistry()
    registry.register("echo", EchoTool)
    executor = ToolExecutor(registry, timeout_seconds=1)
    user_id = uuid4()

    result = await executor.execute(
        "echo",
        {"value": "hello"},
        ToolContext(user_id=user_id, allowed_tools=frozenset({"echo"})),
    )

    assert result.content == "hello"
    assert registry.definitions()[0].name == "echo"

    with pytest.raises(Exception):
        await executor.execute(
            "echo",
            {"value": "blocked"},
            ToolContext(user_id=user_id, allowed_tools=frozenset()),
        )

@pytest.mark.asyncio
async def test_ollama_provider_maps_tool_calls_to_internal_contract() -> None:
    import httpx

    from app.llm.contracts import LLMMessage, LLMMessageRole, LLMRequest, LLMToolDefinition
    from app.llm.providers.ollama import OllamaProvider

    def handler(request: httpx.Request) -> httpx.Response:
        payload = {
            "model": "roleplay-engine",
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "search_knowledge",
                            "arguments": {"query": "Astra Harbor"},
                        }
                    }
                ],
            },
            "done": True,
            "done_reason": "stop",
        }
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="http://ollama.test",
    )
    try:
        provider = OllamaProvider(AppConfig(), client=client)
        response = await provider.chat(
            LLMRequest(
                messages=[LLMMessage(role=LLMMessageRole.USER, content="Find lore")],
                tools=[
                    LLMToolDefinition(
                        name="search_knowledge",
                        description="Search knowledge",
                        input_schema={"type": "object"},
                    )
                ],
            )
        )
    finally:
        await client.aclose()

    assert response.tool_calls[0].name == "search_knowledge"
    assert response.tool_calls[0].arguments == {"query": "Astra Harbor"}
