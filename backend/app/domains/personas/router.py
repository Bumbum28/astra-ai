from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.personas.dependencies import get_persona_service
from app.domains.personas.schemas import (
    PersonaCreateRequest,
    PersonaPageResponse,
    PersonaResponse,
    PersonaUpdateRequest,
)
from app.domains.personas.service import PersonaService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post(
    "",
    response_model=ApiResponse[PersonaResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_persona(
    request: PersonaCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> ApiResponse[PersonaResponse]:
    return ApiResponse[PersonaResponse].ok(
        await service.create(current_user.id, request)
    )


@router.get("", response_model=ApiResponse[PersonaPageResponse])
async def list_personas(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> ApiResponse[PersonaPageResponse]:
    return ApiResponse[PersonaPageResponse].ok(
        await service.list_for_user(current_user.id, limit=limit, cursor=cursor)
    )


@router.get("/{persona_id}", response_model=ApiResponse[PersonaResponse])
async def get_persona(
    persona_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> ApiResponse[PersonaResponse]:
    return ApiResponse[PersonaResponse].ok(
        await service.get(current_user.id, persona_id)
    )


@router.patch("/{persona_id}", response_model=ApiResponse[PersonaResponse])
async def update_persona(
    persona_id: UUID,
    request: PersonaUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> ApiResponse[PersonaResponse]:
    return ApiResponse[PersonaResponse].ok(
        await service.update(current_user.id, persona_id, request)
    )


@router.delete(
    "/{persona_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def archive_persona(
    persona_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> Response:
    await service.archive(current_user.id, persona_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
