from collections.abc import Callable
from typing import cast

from app.core.config import AppConfig
from app.llm.base import BaseLLMProvider
from app.llm.providers.ollama import OllamaProvider
from app.llm.providers.openai import OpenAIProvider
from app.llm.registry import LLMProviderName, ProviderRegistry


def build_default_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(LLMProviderName.OPENAI, OpenAIProvider)
    registry.register(LLMProviderName.OLLAMA, OllamaProvider)
    return registry


class LLMFactory:
    def __init__(self, config: AppConfig, registry: ProviderRegistry) -> None:
        self._config = config
        self._registry = registry

    def get_provider(self, name: LLMProviderName) -> BaseLLMProvider:
        provider_class = self._registry.get(name)
        constructor = cast(Callable[[AppConfig], BaseLLMProvider], provider_class)
        return constructor(self._config)
