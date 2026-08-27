from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.personas.dependencies import get_persona_service
from app.domains.personas.schemas import (
    PersonaCreateRequest,
    PersonaListResponse,
    PersonaResponse,
    PersonaUpdateRequest,
)
from app.domains.personas.service import PersonaService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post("", response_model=ApiResponse[PersonaResponse], status_code=201)
async def create_persona(
    request: PersonaCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> ApiResponse[PersonaResponse]:
    return ApiResponse[PersonaResponse].ok(await service.create(current_user.id, request))


@router.get("", response_model=ApiResponse[PersonaListResponse])
async def list_personas(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> ApiResponse[PersonaListResponse]:
    return ApiResponse[PersonaListResponse].ok(await service.list_for_user(current_user.id))


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


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_persona(
    persona_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[PersonaService, Depends(get_persona_service)],
) -> Response:
    await service.delete(current_user.id, persona_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
