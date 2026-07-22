from collections.abc import AsyncIterator
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import LLMException
from app.core.config import AppConfig
from app.llm.base import BaseLLMProvider
from app.llm.contracts import (
    LLMChunk,
    LLMModelInfo,
    LLMRequest,
    LLMResponse,
    LLMUsage,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Responses API adapter behind Astra's provider-neutral contracts."""

    provider_name = "openai"

    def __init__(
        self,
        config: AppConfig,
        client: AsyncOpenAI | None = None,
    ) -> None:
        api_key = (
            config.openai_api_key.get_secret_value() if config.openai_api_key else None
        )
        if client is None and not api_key:
            raise LLMException(
                "OPENAI_API_KEY is not configured.",
                code=ErrorCode.LLM_NOT_CONFIGURED,
                status_code=503,
            )
        self._default_model = config.default_llm_model
        self._default_reasoning_effort = config.openai_reasoning_effort
        self._store_responses = config.openai_store_responses
        self._client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=config.openai_base_url or None,
            timeout=config.openai_request_timeout_seconds,
            max_retries=config.openai_max_retries,
        )

    async def chat(self, request: LLMRequest) -> LLMResponse:
        kwargs = self._response_kwargs(request)
        try:
            response: Any = await self._client.responses.create(**kwargs)
        except OpenAIError as exc:
            raise LLMException("OpenAI Responses API request failed.") from exc

        content = str(getattr(response, "output_text", "") or "").strip()
        if not content:
            raise LLMException(
                "OpenAI Responses API returned no text output.",
                code=ErrorCode.LLM_PROVIDER_ERROR,
            )
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=content,
            model=str(getattr(response, "model", request.model or self._default_model)),
            provider=self.provider_name,
            finish_reason=self._finish_reason(response),
            provider_response_id=getattr(response, "id", None),
            usage=self._usage(usage),
            metadata={
                "api": "responses",
                "status": getattr(response, "status", None),
                "reasoning_effort": request.reasoning_effort
                or self._default_reasoning_effort,
            },
        )

    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        kwargs = {**self._response_kwargs(request), "stream": True}
        response_id: str | None = None
        model = request.model or self._default_model
        try:
            stream: Any = await self._client.responses.create(**kwargs)
            async for event in stream:
                event_type = str(getattr(event, "type", ""))
                if event_type == "response.created":
                    response = getattr(event, "response", None)
                    response_id = getattr(response, "id", response_id)
                    model = str(getattr(response, "model", model))
                    continue
                if event_type == "response.output_text.delta":
                    yield LLMChunk(
                        content=str(getattr(event, "delta", "") or ""),
                        model=model,
                        provider=self.provider_name,
                        provider_response_id=response_id,
                    )
                    continue
                if event_type == "response.completed":
                    response = getattr(event, "response", None)
                    response_id = getattr(response, "id", response_id)
                    model = str(getattr(response, "model", model))
                    yield LLMChunk(
                        content="",
                        model=model,
                        provider=self.provider_name,
                        finish_reason=self._finish_reason(response),
                        provider_response_id=response_id,
                    )
                    continue
                if event_type == "error":
                    message = getattr(event, "message", None) or "OpenAI stream failed."
                    raise LLMException(str(message))
        except OpenAIError as exc:
            raise LLMException("OpenAI Responses API streaming failed.") from exc

    async def list_models(self) -> list[LLMModelInfo]:
        try:
            models: Any = await self._client.models.list()
        except OpenAIError as exc:
            raise LLMException("Unable to list OpenAI models.") from exc
        return [
            LLMModelInfo(id=model.id, provider=self.provider_name)
            for model in models.data
        ]

    def _response_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        model = request.model or self._default_model
        kwargs: dict[str, Any] = {
            "model": model,
            "input": [
                {
                    "role": message.role.value,
                    "content": message.content,
                }
                for message in request.messages
            ],
            "store": request.store and self._store_responses,
        }
        if request.max_tokens is not None:
            kwargs["max_output_tokens"] = request.max_tokens

        effort = request.reasoning_effort or self._default_reasoning_effort
        if effort:
            kwargs["reasoning"] = {"effort": effort}

        if request.response_schema is not None:
            kwargs["text"] = {
                "format": {
                    "type": "json_schema",
                    "name": request.response_schema_name or "astra_response",
                    "strict": True,
                    "schema": request.response_schema,
                }
            }

        if request.temperature is not None and self._supports_temperature(model):
            kwargs["temperature"] = request.temperature
        return kwargs

    @staticmethod
    def _supports_temperature(model: str) -> bool:
        normalized = model.lower()
        return not normalized.startswith(("gpt-5", "o1", "o3", "o4"))

    @staticmethod
    def _finish_reason(response: Any) -> str | None:
        if response is None:
            return None
        status = getattr(response, "status", None)
        if status == "completed":
            return "stop"
        if status == "incomplete":
            details = getattr(response, "incomplete_details", None)
            return str(getattr(details, "reason", None) or "incomplete")
        return cast(str | None, status)

    @staticmethod
    def _usage(usage: Any) -> LLMUsage | None:
        if usage is None:
            return None
        return LLMUsage(
            input_tokens=getattr(usage, "input_tokens", None),
            output_tokens=getattr(usage, "output_tokens", None),
            total_tokens=getattr(usage, "total_tokens", None),
        )
