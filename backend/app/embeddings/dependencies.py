from typing import Annotated

from fastapi import Depends

from app.core.config import AppConfig, get_config
from app.embeddings.providers.openai import OpenAIEmbeddingProvider
from app.embeddings.service import EmbeddingService


def get_embedding_service(
    config: Annotated[AppConfig, Depends(get_config)],
) -> EmbeddingService:
    has_key = bool(
        config.openai_api_key and config.openai_api_key.get_secret_value().strip()
    )
    if not config.memory_embeddings_enabled or not has_key:
        return EmbeddingService(None)
    return EmbeddingService(OpenAIEmbeddingProvider(config))
