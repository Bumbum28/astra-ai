from collections.abc import AsyncIterator
from typing import Protocol

from app.llm.base import BaseLLMProvider
from app.llm.contracts import LLMChunk, LLMRequest, LLMResponse


class ProviderResolver(Protocol):
    """Resolve an LLM provider without exposing concrete factory implementations."""

    def resolve(self, provider_name: str) -> BaseLLMProvider:
        """Return the provider registered for the supplied name."""
        ...


class ChatService:
    def __init__(self, resolver: ProviderResolver) -> None:
        self._resolver = resolver

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        """Generate a response without depending on any provider SDK."""
        provider = self._resolver.resolve(provider_name)
        return await provider.chat(request)

    def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        """Stream response chunks through the provider-independent contract."""
        provider = self._resolver.resolve(provider_name)
        return provider.stream_chat(request)
