import asyncio
import logging
import signal

from app.core.config import get_config
from app.core.unit_of_work import SQLAlchemyUnitOfWorkFactory
from app.domains.memories.compaction import MemoryCompactionService
from app.embeddings.providers.openai import OpenAIEmbeddingProvider
from app.embeddings.service import EmbeddingService
from app.llm.chat.service import ChatService
from app.llm.factory import LLMFactory, build_default_registry
from app.llm.resolver import LLMProviderResolver
from app.models.loader import load_all_models

logger = logging.getLogger(__name__)


async def run() -> None:
    load_all_models()
    config = get_config()
    uow_factory = SQLAlchemyUnitOfWorkFactory()
    resolver = LLMProviderResolver(LLMFactory(config, build_default_registry()))
    llm = ChatService(resolver)
    has_openai_key = bool(
        config.openai_api_key
        and config.openai_api_key.get_secret_value().strip()
    )
    embedding_provider = (
        OpenAIEmbeddingProvider(config)
        if config.memory_embeddings_enabled and has_openai_key
        else None
    )
    processor = MemoryCompactionService(
        uow_factory,
        llm,
        EmbeddingService(embedding_provider),
        config,
    )
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signal_name in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signal_name, stop.set)

    logger.info("Memory worker started")
    while not stop.is_set():
        task_id = None
        async with uow_factory() as uow:
            task = await uow.memory_tasks.claim_next(
                max_attempts=config.memory_worker_max_attempts,
                lock_timeout_seconds=config.memory_worker_lock_timeout_seconds,
            )
            if task is not None:
                task_id = task.id
                await uow.commit()
        if task_id is None:
            try:
                await asyncio.wait_for(
                    stop.wait(), timeout=config.memory_worker_poll_seconds
                )
            except TimeoutError:
                pass
            continue
        try:
            await processor.process_task(task_id)
        except Exception as exc:
            logger.exception("Memory task %s failed", task_id)
            await processor.mark_failure(task_id, exc)
    logger.info("Memory worker stopped")


if __name__ == "__main__":
    asyncio.run(run())
