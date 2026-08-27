from app.llm.chat.service import ChatService
from app.llm.contracts import LLMRequest, LLMResponse, LLMToolDefinition
from app.tools.registry import ToolRegistry


class ToolCallingService:
    """Expose tool definitions to an LLM without executing an agent loop."""

    def __init__(self, llm_service: ChatService, registry: ToolRegistry) -> None:
        self._llm_service = llm_service
        self._registry = registry

    async def plan(self, provider_name: str, request: LLMRequest) -> LLMResponse:
        definitions = [
            LLMToolDefinition(
                name=item.name,
                description=item.description,
                input_schema=item.input_schema,
            )
            for item in self._registry.definitions()
        ]
        return await self._llm_service.generate(
            provider_name,
            request.model_copy(update={"tools": definitions}),
        )
