from collections.abc import AsyncIterator
from uuid import UUID

from app.agents.runtime import AgentRuntime
from app.agents.schemas import (
    AgentRunListResponse,
    AgentRunResponse,
    AgentStepListResponse,
    AgentStepResponse,
)
from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import NotFoundException
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWorkFactory
from app.llm.contracts import LLMChunk, LLMRequest, LLMResponse


class AgentChatService:
    """Adapter that lets the existing chat pipeline execute through AgentRuntime."""

    def __init__(self, runtime: AgentRuntime, config: AppConfig) -> None:
        self._runtime = runtime
        self._chunk_chars = config.agent_stream_chunk_chars

    async def generate(self, provider_name: str, request: LLMRequest) -> LLMResponse:
        """Execute one bounded Agent run and return its final model response."""
        return await self._runtime.run(provider_name, request)

    async def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        """Execute the Agent and expose its final answer as chat stream chunks."""
        response = await self._runtime.run(provider_name, request)
        content = response.content
        if not content:
            yield LLMChunk(
                content="",
                model=response.model,
                provider=response.provider,
                finish_reason=response.finish_reason,
                provider_response_id=response.provider_response_id,
                usage=response.usage,
                metadata=response.metadata,
            )
            return
        for offset in range(0, len(content), self._chunk_chars):
            end = min(offset + self._chunk_chars, len(content))
            yield LLMChunk(
                content=content[offset:end],
                model=response.model,
                provider=response.provider,
                finish_reason=response.finish_reason if end == len(content) else None,
                provider_response_id=response.provider_response_id,
                usage=response.usage if end == len(content) else None,
                metadata=response.metadata if end == len(content) else {},
            )


class AgentQueryService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    async def list_runs(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID | None = None,
        limit: int = 50,
    ) -> AgentRunListResponse:
        """List Agent runs owned by a user, optionally scoped to a conversation."""
        async with self._uow_factory() as uow:
            items = await uow.agents.list_runs(
                user_id,
                conversation_id=conversation_id,
                limit=limit,
            )
            return AgentRunListResponse(
                items=[AgentRunResponse.model_validate(item) for item in items]
            )

    async def get_run(self, user_id: UUID, run_id: UUID) -> AgentRunResponse:
        """Return one Agent run only when it belongs to the requesting user."""
        async with self._uow_factory() as uow:
            run = await uow.agents.get_run_owned(run_id, user_id)
            if run is None:
                raise NotFoundException(
                    "Agent run was not found.",
                    code=ErrorCode.AGENT_RUN_NOT_FOUND,
                )
            return AgentRunResponse.model_validate(run)

    async def list_steps(
        self,
        user_id: UUID,
        run_id: UUID,
    ) -> AgentStepListResponse:
        """Return ordered execution steps for an Agent run owned by the user."""
        async with self._uow_factory() as uow:
            run = await uow.agents.get_run_owned(run_id, user_id)
            if run is None:
                raise NotFoundException(
                    "Agent run was not found.",
                    code=ErrorCode.AGENT_RUN_NOT_FOUND,
                )
            steps = await uow.agents.list_steps(run_id)
            return AgentStepListResponse(
                items=[AgentStepResponse.model_validate(item) for item in steps]
            )
