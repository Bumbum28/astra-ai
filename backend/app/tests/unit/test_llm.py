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


class FakeOpenAICompletions:
    async def create(self, **_: Any) -> Any:
        return SimpleNamespace(
            id="response-1",
            model="fake-openai-model",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="adapter response"),
                    finish_reason="stop",
                )
            ],
            usage=SimpleNamespace(prompt_tokens=2, completion_tokens=3, total_tokens=5),
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeOpenAICompletions())


@pytest.mark.asyncio
async def test_openai_adapter_maps_to_internal_contract() -> None:
    provider = OpenAIProvider(
        AppConfig(),
        client=cast(AsyncOpenAI, FakeOpenAIClient()),
    )
    response = await provider.chat(
        LLMRequest(messages=[LLMMessage(role=LLMMessageRole.USER, content="hello")])
    )
    assert response.content == "adapter response"
    assert response.provider == "openai"
    assert response.usage is not None
    assert response.usage.total_tokens == 5


def test_openai_gpt56_uses_reasoning_compatible_chat_parameters() -> None:
    request = LLMRequest(
        model="gpt-5.6-terra",
        messages=[LLMMessage(role=LLMMessageRole.USER, content="hello")],
        temperature=0.8,
        max_tokens=2048,
    )
    kwargs = OpenAIProvider._completion_kwargs(
        request,
        model="gpt-5.6-terra",
        messages=[],
        stream=True,
    )

    assert kwargs["max_completion_tokens"] == 2048
    assert "max_tokens" not in kwargs
    assert "temperature" not in kwargs
    assert kwargs["stream"] is True


def test_openai_non_reasoning_model_preserves_sampling_parameters() -> None:
    request = LLMRequest(
        model="gpt-4.1-mini",
        messages=[LLMMessage(role=LLMMessageRole.USER, content="hello")],
        temperature=0.7,
        max_tokens=1024,
    )
    kwargs = OpenAIProvider._completion_kwargs(
        request,
        model="gpt-4.1-mini",
        messages=[],
        stream=False,
    )

    assert kwargs["max_tokens"] == 1024
    assert "max_completion_tokens" not in kwargs
    assert kwargs["temperature"] == 0.7
    assert kwargs["stream"] is False
