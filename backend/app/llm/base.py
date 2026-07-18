from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.llm.contracts import LLMChunk, LLMModelInfo, LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    provider_name: str

    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Generate one complete provider-independent response."""

    @abstractmethod
    def stream_chat(self, request: LLMRequest) -> AsyncIterator[LLMChunk]:
        """Stream provider-independent chunks."""

    @abstractmethod
    async def list_models(self) -> list[LLMModelInfo]:
        """Return models exposed by the configured provider account."""
