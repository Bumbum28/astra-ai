from openai import AsyncOpenAI, OpenAIError

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import LLMException
from app.core.config import AppConfig
from app.embeddings.base import BaseEmbeddingProvider


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self,
        config: AppConfig,
        client: AsyncOpenAI | None = None,
    ) -> None:
        api_key = (
            config.openai_api_key.get_secret_value() if config.openai_api_key else None
        )
        if client is None and not api_key:
            raise LLMException(
                "OPENAI_API_KEY is required for memory embeddings.",
                code=ErrorCode.LLM_NOT_CONFIGURED,
                status_code=503,
            )
        self._model = config.memory_embedding_model
        self._dimensions = config.memory_embedding_dimensions
        self._client = client or AsyncOpenAI(
            api_key=api_key,
            base_url=config.openai_base_url or None,
            timeout=config.openai_request_timeout_seconds,
            max_retries=config.openai_max_retries,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self._client.embeddings.create(
                model=self._model,
                input=texts,
                dimensions=self._dimensions,
                encoding_format="float",
            )
        except OpenAIError as exc:
            raise LLMException("OpenAI embedding request failed.") from exc
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]
