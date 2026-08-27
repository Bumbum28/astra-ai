from hashlib import sha256
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.domains.knowledge.chunker import chunk_text
from app.domains.knowledge.model import (
    KnowledgeChunk,
    KnowledgeSource,
    KnowledgeSourceStatus,
)
from app.domains.knowledge.schemas import (
    KnowledgeSearchHit,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceCreateRequest,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)
from app.rag.contracts import RetrievalQuery
from app.rag.service import RAGService


class KnowledgeService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        rag_service: RAGService,
        config: AppConfig,
    ) -> None:
        self._uow_factory = uow_factory
        self._rag_service = rag_service
        self._config = config

    async def create_source(
        self, user_id: UUID, request: KnowledgeSourceCreateRequest
    ) -> KnowledgeSourceResponse:
        """Persist a text source and deterministic chunks for retrieval."""
        source = KnowledgeSource(
            id=uuid4(),
            user_id=user_id,
            name=request.name,
            source_type=request.source_type,
            status=KnowledgeSourceStatus.READY,
            source_metadata=request.metadata,
        )
        chunks = chunk_text(
            request.content,
            size=self._config.rag_chunk_size_chars,
            overlap=self._config.rag_chunk_overlap_chars,
        )
        orm_chunks = [
            KnowledgeChunk(
                id=uuid4(),
                source_id=source.id,
                user_id=user_id,
                ordinal=item.ordinal,
                content=item.content,
                content_hash=sha256(item.content.encode("utf-8")).hexdigest(),
                token_estimate=max(len(item.content) // 4, 1),
                chunk_metadata={},
            )
            for item in chunks
        ]
        async with self._uow_factory() as uow:
            await uow.knowledge.add_source(source)
            await uow.knowledge.add_chunks(orm_chunks)
            await uow.flush()
            response = KnowledgeSourceResponse.model_validate(source)
            await uow.commit()
            return response

    async def list_sources(self, user_id: UUID) -> KnowledgeSourceListResponse:
        """List active knowledge sources owned by a user."""
        async with self._uow_factory() as uow:
            items = await uow.knowledge.list_sources(user_id)
        return KnowledgeSourceListResponse(
            items=[KnowledgeSourceResponse.model_validate(item) for item in items]
        )

    async def search(
        self, user_id: UUID, request: KnowledgeSearchRequest
    ) -> KnowledgeSearchResponse:
        """Run RAG retrieval through the storage-independent RAG service."""
        hits = await self._rag_service.search(
            RetrievalQuery(
                user_id=user_id,
                query=request.query,
                top_k=request.top_k,
                source_ids=tuple(request.source_ids),
            )
        )
        return KnowledgeSearchResponse(
            items=[KnowledgeSearchHit(**hit.model_dump()) for hit in hits]
        )

    async def archive(self, user_id: UUID, source_id: UUID) -> None:
        """Archive a source so its chunks stop participating in retrieval."""
        async with self._uow_factory() as uow:
            source = await uow.knowledge.get_source_owned(
                source_id, user_id, for_update=True
            )
            if source is None:
                raise NotFoundException(
                    "Knowledge source was not found.",
                    code=ErrorCode.KNOWLEDGE_SOURCE_NOT_FOUND,
                )
            source.status = KnowledgeSourceStatus.ARCHIVED
            await uow.commit()
