from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.memories.dependencies import get_memory_service
from app.domains.memories.model import MemoryScope
from app.domains.memories.schemas import (
    ConversationMemorySnapshot,
    MemoryCreateRequest,
    MemoryPage,
    MemoryRefreshResponse,
    MemoryResponse,
    MemoryUpdateRequest,
)
from app.domains.memories.service import MemoryService
from app.domains.users.schemas import UserResponse

router = APIRouter(tags=["Memory"])


@router.post(
    "/memories",
    response_model=ApiResponse[MemoryResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_memory(
    request: MemoryCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[MemoryResponse]:
    created = await service.create(current_user.id, request)
    return ApiResponse[MemoryResponse].ok(created)


@router.get("/memories", response_model=ApiResponse[MemoryPage])
async def list_memories(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    cursor: str | None = None,
    scope: MemoryScope | None = None,
    conversation_id: UUID | None = None,
    include_archived: bool = False,
) -> ApiResponse[MemoryPage]:
    return ApiResponse[MemoryPage].ok(
        await service.list_for_user(
            current_user.id,
            limit=limit,
            cursor=cursor,
            scope=scope,
            conversation_id=conversation_id,
            include_archived=include_archived,
        )
    )


@router.patch("/memories/{memory_id}", response_model=ApiResponse[MemoryResponse])
async def update_memory(
    memory_id: UUID,
    request: MemoryUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[MemoryResponse]:
    return ApiResponse[MemoryResponse].ok(
        await service.update(current_user.id, memory_id, request)
    )


@router.delete(
    "/memories/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def archive_memory(
    memory_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> Response:
    await service.archive(current_user.id, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/conversations/{conversation_id}/memory",
    response_model=ApiResponse[ConversationMemorySnapshot],
)
async def conversation_memory(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[ConversationMemorySnapshot]:
    return ApiResponse[ConversationMemorySnapshot].ok(
        await service.conversation_snapshot(current_user.id, conversation_id)
    )


@router.post(
    "/conversations/{conversation_id}/memory/refresh",
    response_model=ApiResponse[MemoryRefreshResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_conversation_memory(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[MemoryRefreshResponse]:
    return ApiResponse[MemoryRefreshResponse].ok(
        await service.refresh(current_user.id, conversation_id)
    )
