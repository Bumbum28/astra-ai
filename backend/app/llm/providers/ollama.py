import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import LLMException
from app.core.config import AppConfig
from app.llm.base import BaseLLMProvider
from app.llm.contracts import (
    LLMChunk,
    LLMModelInfo,
    LLMRequest,
    LLMResponse,
    LLMToolCall,
    LLMUsage,
)


class OllamaProvider(BaseLLMProvider):
    """Native Ollama adapter that exposes Astra's provider-independent contracts."""

    provider_name = "ollama"

    def __init__(
        self,
        config: AppConfig,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = config.ollama_base_url.rstrip("/")
        self._default_model = config.ollama_default_model
        self._timeout = config.ollama_request_timeout_seconds
        self._client = client

    @asynccontextmanager
    async def _client_context(self) -> AsyncIterator[httpx.AsyncClient]:
        if self._client is not None:
            yield self._client
            return

        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
        ) as client:
            yield client

    def _build_payload(self, request: LLMRequest, *, stream: bool) -> dict[str, Any]:
        options: dict[str, Any] = {}
        if request.temperature is not None:
            options["temperature"] = request.temperature
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens

        payload: dict[str, Any] = {
            "model": request.model or self._default_model,
            "messages": [
                {
                    "role": message.role.value,
                    "content": message.content,
                    **({"name": message.name} if message.name else {}),
                    **(
                        {"tool_call_id": message.tool_call_id}
                        if message.tool_call_id
                        else {}
                    ),
                    **(
                        {
                            "tool_calls": [
                                {
                                    "id": call.id,
                                    "function": {
                                        "name": call.name,
                                        "arguments": call.arguments,
                                    },
                                }
                                for call in message.tool_calls
                            ]
                        }
                        if message.tool_calls
                        else {}
                    ),
                }
                for message in request.messages
            ],
            "stream": stream,
        }
        if request.tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
                for tool in request.tools
            ]
        if options:
            payload["options"] = options
        return payload

    async def chat(self, request: LLMRequest) -> LLMResponse:
        payload = self._build_payload(request, stream=False)
        try:
            async with self._client_context() as client:
                response = await client.post("/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMException(
                "Ollama request failed.",
                code=ErrorCode.LLM_PROVIDER_ERROR,
            ) from exc

        message = data.get("message") or {}
        tool_calls: list[LLMToolCall] = []
        for index, item in enumerate(message.get("tool_calls") or []):
            function = item.get("function") or {}
            arguments = function.get("arguments")
            tool_calls.append(
                LLMToolCall(
                    id=str(item.get("id") or f"ollama-tool-{index}"),
                    name=str(function.get("name") or ""),
                    arguments=arguments if isinstance(arguments, dict) else {},
                )
            )
        input_tokens = data.get("prompt_eval_count")
        output_tokens = data.get("eval_count")
        total_tokens = None
        if isinstance(input_tokens, int) and isinstance(output_tokens, int):
            total_tokens = input_tokens + output_tokens

        return LLMResponse(
            content=str(message.get("content") or ""),
            model=str(data.get("model") or payload["model"]),
            provider=self.provider_name,
            finish_reason=str(data.get("done_reason") or "stop"),
            tool_calls=tool_calls,
            usage=LLMUsage(
                input_tokens=input_tokens if isinstance(input_tokens, int) else None,
                output_tokens=(
                    output_tokens if isinstance(output_tokens, int) else None
                ),
                total_tokens=total_tokens,
            ),
            metadata={"done": bool(data.get("done", True))},
        )

    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        payload = self._build_payload(request, stream=True)
        try:
            async with (
                self._client_context() as client,
                client.stream("POST", "/api/chat", json=payload) as response,
            ):
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise LLMException(
                            "Ollama returned an invalid streaming payload."
                        ) from exc

                    message = data.get("message") or {}
                    yield LLMChunk(
                        content=str(message.get("content") or ""),
                        model=str(data.get("model") or payload["model"]),
                        provider=self.provider_name,
                        finish_reason=(
                            str(data.get("done_reason") or "stop")
                            if data.get("done")
                            else None
                        ),
                    )
        except httpx.HTTPError as exc:
            raise LLMException("Ollama streaming request failed.") from exc

    async def list_models(self) -> list[LLMModelInfo]:
        try:
            async with self._client_context() as client:
                response = await client.get("/api/tags")
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMException("Unable to list Ollama models.") from exc

        result: list[LLMModelInfo] = []
        for model in data.get("models", []):
            model_id = model.get("name") or model.get("model")
            if not model_id:
                continue
            result.append(
                LLMModelInfo(
                    id=str(model_id),
                    provider=self.provider_name,
                    capabilities={"chat", "streaming"},
                    metadata={
                        "size": model.get("size"),
                        "modified_at": model.get("modified_at"),
                    },
                )
            )
        return result
