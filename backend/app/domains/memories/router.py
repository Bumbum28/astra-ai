from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.memories.dependencies import get_memory_service
from app.domains.memories.schemas import MemoryCreateRequest, MemoryListResponse, MemoryResponse
from app.domains.memories.service import MemoryService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/memories", tags=["Memories"])


@router.post("", response_model=ApiResponse[MemoryResponse], status_code=201)
async def create_memory(
    request: MemoryCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[MemoryResponse]:
    return ApiResponse[MemoryResponse].ok(await service.create(current_user.id, request))


@router.get("", response_model=ApiResponse[MemoryListResponse])
async def list_memories(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> ApiResponse[MemoryListResponse]:
    return ApiResponse[MemoryListResponse].ok(await service.list_for_user(current_user.id))


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def archive_memory(
    memory_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[MemoryService, Depends(get_memory_service)],
) -> Response:
    await service.archive(current_user.id, memory_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
