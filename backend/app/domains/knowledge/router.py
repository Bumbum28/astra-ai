from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.knowledge.dependencies import get_knowledge_service
from app.domains.knowledge.schemas import (
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceCreateRequest,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
)
from app.domains.knowledge.service import KnowledgeService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.post("/sources", response_model=ApiResponse[KnowledgeSourceResponse], status_code=201)
async def create_source(
    request: KnowledgeSourceCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> ApiResponse[KnowledgeSourceResponse]:
    return ApiResponse[KnowledgeSourceResponse].ok(
        await service.create_source(current_user.id, request)
    )


@router.get("/sources", response_model=ApiResponse[KnowledgeSourceListResponse])
async def list_sources(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> ApiResponse[KnowledgeSourceListResponse]:
    return ApiResponse[KnowledgeSourceListResponse].ok(
        await service.list_sources(current_user.id)
    )


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def archive_source(
    source_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> Response:
    await service.archive(current_user.id, source_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/search", response_model=ApiResponse[KnowledgeSearchResponse])
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
) -> ApiResponse[KnowledgeSearchResponse]:
    return ApiResponse[KnowledgeSearchResponse].ok(
        await service.search(current_user.id, request)
    )
