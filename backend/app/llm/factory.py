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
        self._instances: dict[LLMProviderName, BaseLLMProvider] = {}

    def get_provider(self, name: LLMProviderName) -> BaseLLMProvider:
        provider = self._instances.get(name)
        if provider is not None:
            return provider
        provider_class = self._registry.get(name)
        constructor = cast(Callable[[AppConfig], BaseLLMProvider], provider_class)
        provider = constructor(self._config)
        self._instances[name] = provider
        return provider
