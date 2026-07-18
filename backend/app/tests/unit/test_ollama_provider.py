import json

import httpx
import pytest

from app.core.config import AppConfig
from app.llm.contracts import LLMMessage, LLMMessageRole, LLMRequest
from app.llm.factory import LLMFactory, build_default_registry
from app.llm.providers.ollama import OllamaProvider
from app.llm.registry import LLMProviderName


def build_client(handler: httpx.MockTransport) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=handler,
        base_url="http://ollama.test",
    )


@pytest.mark.asyncio
async def test_ollama_chat_maps_native_response_to_contract() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content)
        assert payload["model"] == "roleplay-engine"
        assert payload["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "roleplay-engine",
                "message": {"role": "assistant", "content": "Xin chào."},
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": 7,
                "eval_count": 3,
            },
        )

    async with build_client(httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(AppConfig(), client=client)
        response = await provider.chat(
            LLMRequest(
                messages=[LLMMessage(role=LLMMessageRole.USER, content="Chào nhân vật")]
            )
        )

    assert response.content == "Xin chào."
    assert response.provider == "ollama"
    assert response.model == "roleplay-engine"
    assert response.usage is not None
    assert response.usage.total_tokens == 10


@pytest.mark.asyncio
async def test_ollama_stream_maps_ndjson_chunks() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = "\n".join(
            [
                json.dumps(
                    {
                        "model": "roleplay-engine",
                        "message": {"content": "Xin "},
                        "done": False,
                    }
                ),
                json.dumps(
                    {
                        "model": "roleplay-engine",
                        "message": {"content": "chào."},
                        "done": True,
                        "done_reason": "stop",
                    }
                ),
            ]
        )
        return httpx.Response(200, content=body.encode())

    async with build_client(httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(AppConfig(), client=client)
        chunks = [
            chunk
            async for chunk in provider.stream_chat(
                LLMRequest(
                    messages=[LLMMessage(role=LLMMessageRole.USER, content="Chào")]
                )
            )
        ]

    assert [chunk.content for chunk in chunks] == ["Xin ", "chào."]
    assert chunks[-1].finish_reason == "stop"


@pytest.mark.asyncio
async def test_ollama_lists_local_models() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tags"
        return httpx.Response(
            200,
            json={
                "models": [
                    {
                        "name": "roleplay-engine:latest",
                        "size": 123,
                        "modified_at": "2026-07-18T00:00:00Z",
                    }
                ]
            },
        )

    async with build_client(httpx.MockTransport(handler)) as client:
        provider = OllamaProvider(AppConfig(), client=client)
        models = await provider.list_models()

    assert len(models) == 1
    assert models[0].id == "roleplay-engine:latest"
    assert "streaming" in models[0].capabilities


def test_default_registry_contains_ollama_provider() -> None:
    factory = LLMFactory(AppConfig(), build_default_registry())
    provider = factory.get_provider(LLMProviderName.OLLAMA)

    assert isinstance(provider, OllamaProvider)
