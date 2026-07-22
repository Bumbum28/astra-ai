from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.relationships.dependencies import get_relationship_service
from app.domains.relationships.schemas import (
    RelationshipHistoryResponse,
    RelationshipResponse,
    RelationshipUpdateRequest,
)
from app.domains.relationships.service import RelationshipService
from app.domains.users.schemas import UserResponse

router = APIRouter(tags=["Relationships"])


@router.get(
    "/conversations/{conversation_id}/relationship",
    response_model=ApiResponse[RelationshipResponse],
)
async def get_relationship(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[RelationshipService, Depends(get_relationship_service)],
) -> ApiResponse[RelationshipResponse]:
    return ApiResponse[RelationshipResponse].ok(
        await service.get(current_user.id, conversation_id)
    )


@router.patch(
    "/conversations/{conversation_id}/relationship",
    response_model=ApiResponse[RelationshipResponse],
)
async def update_relationship(
    conversation_id: UUID,
    request: RelationshipUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[RelationshipService, Depends(get_relationship_service)],
) -> ApiResponse[RelationshipResponse]:
    return ApiResponse[RelationshipResponse].ok(
        await service.update(current_user.id, conversation_id, request)
    )


@router.get(
    "/conversations/{conversation_id}/relationship/events",
    response_model=ApiResponse[RelationshipHistoryResponse],
)
async def relationship_history(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[RelationshipService, Depends(get_relationship_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ApiResponse[RelationshipHistoryResponse]:
    return ApiResponse[RelationshipHistoryResponse].ok(
        await service.history(current_user.id, conversation_id, limit=limit)
    )
