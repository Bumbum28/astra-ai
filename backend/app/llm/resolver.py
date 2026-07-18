from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import LLMException
from app.llm.base import BaseLLMProvider
from app.llm.factory import LLMFactory
from app.llm.registry import LLMProviderName


class LLMProviderResolver:
    def __init__(self, factory: LLMFactory) -> None:
        self._factory = factory

    def resolve(self, provider_name: str | LLMProviderName) -> BaseLLMProvider:
        try:
            name = LLMProviderName(provider_name)
        except ValueError as exc:
            raise LLMException(
                f"Unknown LLM provider '{provider_name}'.",
                code=ErrorCode.LLM_PROVIDER_NOT_FOUND,
            ) from exc
        return self._factory.get_provider(name)
