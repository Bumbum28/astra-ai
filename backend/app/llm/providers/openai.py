import json
from collections.abc import AsyncIterator
from typing import Any, cast

from openai import AsyncOpenAI, OpenAIError, omit
from openai.types.chat import ChatCompletionMessageParam

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


class OpenAIProvider(BaseLLMProvider):
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
        self._client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=config.openai_base_url,
        )

    async def chat(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self._default_model
        messages = self._build_messages(request)
        try:
            response: Any = await self._client.chat.completions.create(
                **self._completion_kwargs(
                    request,
                    model=model,
                    messages=messages,
                    stream=False,
                )
            )
        except OpenAIError as exc:
            raise self._provider_error(exc, model=model, streaming=False) from exc

        choice = response.choices[0]
        usage = response.usage
        tool_calls: list[LLMToolCall] = []
        for item in choice.message.tool_calls or []:
            try:
                arguments = json.loads(item.function.arguments or "{}")
            except json.JSONDecodeError:
                arguments = {"_raw": item.function.arguments}
            tool_calls.append(
                LLMToolCall(
                    id=item.id,
                    name=item.function.name,
                    arguments=arguments,
                )
            )
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider=self.provider_name,
            finish_reason=choice.finish_reason,
            provider_response_id=response.id,
            tool_calls=tool_calls,
            usage=(
                LLMUsage(
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                )
                if usage
                else None
            ),
        )

    async def stream_chat(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        model = request.model or self._default_model
        messages = self._build_messages(request)
        try:
            stream: Any = await self._client.chat.completions.create(
                **self._completion_kwargs(
                    request,
                    model=model,
                    messages=messages,
                    stream=True,
                )
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                choice = chunk.choices[0]
                yield LLMChunk(
                    content=choice.delta.content or "",
                    model=chunk.model,
                    provider=self.provider_name,
                    finish_reason=choice.finish_reason,
                    provider_response_id=chunk.id,
                )
        except OpenAIError as exc:
            raise self._provider_error(exc, model=model, streaming=True) from exc

    async def list_models(self) -> list[LLMModelInfo]:
        try:
            models: Any = await self._client.models.list()
        except OpenAIError as exc:
            raise LLMException("Unable to list OpenAI models.") from exc
        return [
            LLMModelInfo(id=model.id, provider=self.provider_name)
            for model in models.data
        ]

    @staticmethod
    def _build_messages(request: LLMRequest) -> list[ChatCompletionMessageParam]:
        return [
            cast(
                ChatCompletionMessageParam,
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
                                    "type": "function",
                                    "function": {
                                        "name": call.name,
                                        "arguments": json.dumps(call.arguments),
                                    },
                                }
                                for call in message.tool_calls
                            ]
                        }
                        if message.tool_calls
                        else {}
                    ),
                },
            )
            for message in request.messages
        ]

    @classmethod
    def _completion_kwargs(
        cls,
        request: LLMRequest,
        *,
        model: str,
        messages: list[ChatCompletionMessageParam],
        stream: bool,
    ) -> dict[str, Any]:
        """Build model-compatible Chat Completions parameters.

        Newer reasoning families reject legacy sampling/output parameters in
        configurations where reasoning is enabled. Astra keeps the internal
        provider-neutral request stable and adapts only at the provider edge.
        """
        reasoning_model = cls._is_reasoning_model(model)
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "tools": (
                [
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
                if request.tools
                else omit
            ),
            "tool_choice": request.tool_choice if request.tool_choice else omit,
        }

        if request.max_tokens is not None:
            if reasoning_model:
                kwargs["max_completion_tokens"] = request.max_tokens
            else:
                kwargs["max_tokens"] = request.max_tokens

        # GPT-5/o-series reasoning defaults can reject custom temperature.
        # Omit it rather than silently forcing reasoning off. A future explicit
        # reasoning contract can expose effort without coupling Chat to OpenAI.
        if request.temperature is not None and not reasoning_model:
            kwargs["temperature"] = request.temperature

        return kwargs

    @staticmethod
    def _is_reasoning_model(model: str) -> bool:
        normalized = model.lower()
        return normalized.startswith(("gpt-5", "o1", "o3", "o4"))

    @staticmethod
    def _provider_error(
        exc: OpenAIError,
        *,
        model: str,
        streaming: bool,
    ) -> LLMException:
        message = getattr(exc, "message", None) or str(exc)
        safe_message = " ".join(str(message).split())[:500]
        return LLMException(
            "OpenAI streaming request failed."
            if streaming
            else "OpenAI request failed.",
            details={
                "provider": "openai",
                "model": model,
                "provider_message": safe_message,
            },
        )
