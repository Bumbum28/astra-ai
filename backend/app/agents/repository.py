from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.model import AgentRun, AgentStep


class AgentRepository(Protocol):
    async def add_run(self, run: AgentRun) -> None: ...

    async def add_step(self, step: AgentStep) -> None: ...

    async def get_run(
        self,
        run_id: UUID,
        *,
        for_update: bool = False,
    ) -> AgentRun | None: ...

    async def get_run_owned(
        self,
        run_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> AgentRun | None: ...

    async def list_runs(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID | None = None,
        limit: int = 50,
    ) -> Sequence[AgentRun]: ...

    async def list_steps(self, run_id: UUID) -> Sequence[AgentStep]: ...


class SQLAlchemyAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_run(self, run: AgentRun) -> None:
        self._session.add(run)

    async def add_step(self, step: AgentStep) -> None:
        self._session.add(step)

    async def get_run(
        self,
        run_id: UUID,
        *,
        for_update: bool = False,
    ) -> AgentRun | None:
        statement = select(AgentRun).where(AgentRun.id == run_id)
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def get_run_owned(
        self,
        run_id: UUID,
        user_id: UUID,
        *,
        for_update: bool = False,
    ) -> AgentRun | None:
        statement = select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.user_id == user_id,
        )
        if for_update:
            statement = statement.with_for_update()
        result = await self._session.execute(statement)
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        user_id: UUID,
        *,
        conversation_id: UUID | None = None,
        limit: int = 50,
    ) -> Sequence[AgentRun]:
        statement = select(AgentRun).where(AgentRun.user_id == user_id)
        if conversation_id is not None:
            statement = statement.where(AgentRun.conversation_id == conversation_id)
        statement = statement.order_by(AgentRun.started_at.desc()).limit(limit)
        result = await self._session.execute(statement)
        return result.scalars().all()

    async def list_steps(self, run_id: UUID) -> Sequence[AgentStep]:
        statement = (
            select(AgentStep)
            .where(AgentStep.agent_run_id == run_id)
            .order_by(AgentStep.step_number.asc())
        )
        result = await self._session.execute(statement)
        return result.scalars().all()
