from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.agents.dependencies import get_agent_query_service
from app.agents.schemas import (
    AgentRunListResponse,
    AgentRunResponse,
    AgentStepListResponse,
)
from app.agents.service import AgentQueryService
from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/agent-runs", tags=["Agents"])


@router.get("", response_model=ApiResponse[AgentRunListResponse])
async def list_agent_runs(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AgentQueryService, Depends(get_agent_query_service)],
    conversation_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[AgentRunListResponse]:
    return ApiResponse[AgentRunListResponse].ok(
        await service.list_runs(
            current_user.id,
            conversation_id=conversation_id,
            limit=limit,
        )
    )


@router.get("/{run_id}", response_model=ApiResponse[AgentRunResponse])
async def get_agent_run(
    run_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AgentQueryService, Depends(get_agent_query_service)],
) -> ApiResponse[AgentRunResponse]:
    return ApiResponse[AgentRunResponse].ok(
        await service.get_run(current_user.id, run_id)
    )


@router.get("/{run_id}/steps", response_model=ApiResponse[AgentStepListResponse])
async def list_agent_steps(
    run_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[AgentQueryService, Depends(get_agent_query_service)],
) -> ApiResponse[AgentStepListResponse]:
    return ApiResponse[AgentStepListResponse].ok(
        await service.list_steps(current_user.id, run_id)
    )
