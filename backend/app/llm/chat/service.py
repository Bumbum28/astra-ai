from app.llm.contracts import LLMRequest, LLMResponse
from app.llm.resolver import LLMProviderResolver


class ChatService:
    def __init__(self, resolver: LLMProviderResolver) -> None:
        self._resolver = resolver

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        """Generate a response without depending on any provider SDK."""
        provider = self._resolver.resolve(provider_name)
        return await provider.chat(request)
