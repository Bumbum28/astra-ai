from enum import StrEnum

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import LLMException
from app.llm.base import BaseLLMProvider


class LLMProviderName(StrEnum):
    OPENAI = "openai"
    OLLAMA = "ollama"


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[LLMProviderName, type[BaseLLMProvider]] = {}

    def register(
        self,
        name: LLMProviderName,
        provider_class: type[BaseLLMProvider],
        *,
        replace: bool = False,
    ) -> None:
        if name in self._providers and not replace:
            raise ValueError(f"Provider '{name}' is already registered.")
        self._providers[name] = provider_class

    def get(self, name: LLMProviderName) -> type[BaseLLMProvider]:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise LLMException(
                f"LLM provider '{name}' is not registered.",
                code=ErrorCode.LLM_PROVIDER_NOT_FOUND,
            ) from exc

    def copy(self) -> "ProviderRegistry":
        registry = ProviderRegistry()
        registry._providers = self._providers.copy()
        return registry
