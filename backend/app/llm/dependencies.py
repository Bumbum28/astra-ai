from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.llm.chat.service import ChatService
from app.llm.factory import LLMFactory, build_default_registry
from app.llm.registry import ProviderRegistry
from app.llm.resolver import LLMProviderResolver


@lru_cache
def get_provider_registry() -> ProviderRegistry:
    return build_default_registry()


def get_llm_factory(
    config: Annotated[AppConfig, Depends(get_config)],
    registry: Annotated[ProviderRegistry, Depends(get_provider_registry)],
) -> LLMFactory:
    return LLMFactory(config, registry)


def get_llm_resolver(
    factory: Annotated[LLMFactory, Depends(get_llm_factory)],
) -> LLMProviderResolver:
    return LLMProviderResolver(factory)


def get_llm_chat_service(
    resolver: Annotated[LLMProviderResolver, Depends(get_llm_resolver)],
) -> ChatService:
    return ChatService(resolver)
