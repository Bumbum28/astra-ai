from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any, cast

import pytest
from openai import AsyncOpenAI

from app.core.config import AppConfig
from app.llm.base import BaseLLMProvider
from app.llm.chat.service import ChatService
from app.llm.contracts import (
    LLMChunk,
    LLMMessage,
    LLMMessageRole,
    LLMModelInfo,
    LLMRequest,
    LLMResponse,
)
from app.llm.factory import LLMFactory
from app.llm.providers.openai import OpenAIProvider
from app.llm.registry import LLMProviderName, ProviderRegistry
from app.llm.resolver import LLMProviderResolver


class FakeProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(self, config: AppConfig) -> None:
        self._config = config

    async def chat(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="fake response",
            model=request.model or "fake-model",
            provider=self.provider_name,
        )

    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        yield LLMChunk(
            content="fake",
            model=request.model or "fake-model",
            provider=self.provider_name,
        )

    async def list_models(self) -> list[LLMModelInfo]:
        return [LLMModelInfo(id="fake-model", provider=self.provider_name)]


@pytest.mark.asyncio
async def test_chat_service_uses_provider_abstraction() -> None:
    registry = ProviderRegistry()
    registry.register(LLMProviderName.OPENAI, FakeProvider)
    resolver = LLMProviderResolver(LLMFactory(AppConfig(), registry))
    service = ChatService(resolver)
    response = await service.generate(
        "openai",
        LLMRequest(messages=[LLMMessage(role=LLMMessageRole.USER, content="hello")]),
    )
    assert response.content == "fake response"
    assert response.provider == "openai"


class FakeOpenAIResponses:
    def __init__(self) -> None:
        self.last_kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> Any:
        self.last_kwargs = kwargs
        return SimpleNamespace(
            id="response-1",
            model="gpt-5.6-terra",
            output_text="adapter response",
            status="completed",
            usage=SimpleNamespace(input_tokens=2, output_tokens=3, total_tokens=5),
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.responses = FakeOpenAIResponses()


@pytest.mark.asyncio
async def test_openai_adapter_maps_responses_api_to_internal_contract() -> None:
    client = FakeOpenAIClient()
    provider = OpenAIProvider(
        AppConfig(),
        client=cast(AsyncOpenAI, client),
    )
    response = await provider.chat(
        LLMRequest(
            messages=[LLMMessage(role=LLMMessageRole.USER, content="hello")],
            model="gpt-5.6-terra",
            reasoning_effort="medium",
        )
    )
    assert response.content == "adapter response"
    assert response.provider == "openai"
    assert response.usage is not None
    assert response.usage.total_tokens == 5
    assert response.metadata["api"] == "responses"
    assert client.responses.last_kwargs["reasoning"] == {"effort": "medium"}
    assert client.responses.last_kwargs["store"] is False


@pytest.mark.asyncio
async def test_openai_adapter_maps_structured_output_schema() -> None:
    client = FakeOpenAIClient()
    provider = OpenAIProvider(
        AppConfig(),
        client=cast(AsyncOpenAI, client),
    )
    schema = {
        "type": "object",
        "properties": {"approved": {"type": "boolean"}},
        "required": ["approved"],
        "additionalProperties": False,
    }

    await provider.chat(
        LLMRequest(
            messages=[LLMMessage(role=LLMMessageRole.USER, content="review")],
            response_schema_name="critic",
            response_schema=schema,
        )
    )

    assert client.responses.last_kwargs["text"] == {
        "format": {
            "type": "json_schema",
            "name": "critic",
            "strict": True,
            "schema": schema,
        }
    }


def test_factory_reuses_provider_instance() -> None:
    registry = ProviderRegistry()
    registry.register(LLMProviderName.OPENAI, FakeProvider)
    factory = LLMFactory(AppConfig(), registry)

    first = factory.get_provider(LLMProviderName.OPENAI)
    second = factory.get_provider(LLMProviderName.OPENAI)

    assert first is second

