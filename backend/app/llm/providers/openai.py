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
        messages = [
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
        try:
            response = await self._client.chat.completions.create(
                model=request.model or self._default_model,
                messages=messages,
                temperature=(
                    request.temperature if request.temperature is not None else omit
                ),
                max_tokens=(
                    request.max_tokens if request.max_tokens is not None else omit
                ),
                tools=(
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
                tool_choice=(request.tool_choice if request.tool_choice else omit),
            )
        except OpenAIError as exc:
            raise LLMException("OpenAI request failed.") from exc

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
        messages = [
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
        try:
            stream = await self._client.chat.completions.create(
                model=request.model or self._default_model,
                messages=messages,
                temperature=(
                    request.temperature if request.temperature is not None else omit
                ),
                max_tokens=(
                    request.max_tokens if request.max_tokens is not None else omit
                ),
                tools=(
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
                tool_choice=(request.tool_choice if request.tool_choice else omit),
                stream=True,
            )
            async for chunk in stream:
                choice = chunk.choices[0]
                yield LLMChunk(
                    content=choice.delta.content or "",
                    model=chunk.model,
                    provider=self.provider_name,
                    finish_reason=choice.finish_reason,
                    provider_response_id=chunk.id,
                )
        except OpenAIError as exc:
            raise LLMException("OpenAI streaming request failed.") from exc

    async def list_models(self) -> list[LLMModelInfo]:
        try:
            models: Any = await self._client.models.list()
        except OpenAIError as exc:
            raise LLMException("Unable to list OpenAI models.") from exc
        return [
            LLMModelInfo(id=model.id, provider=self.provider_name)
            for model in models.data
        ]
