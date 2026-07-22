from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.characters.dependencies import get_character_service
from app.domains.characters.schemas import (
    CharacterCreateRequest,
    CharacterPageResponse,
    CharacterResponse,
    CharacterUpdateRequest,
)
from app.domains.characters.service import CharacterService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/characters", tags=["Characters"])


@router.post(
    "",
    response_model=ApiResponse[CharacterResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_character(
    request: CharacterCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> ApiResponse[CharacterResponse]:
    return ApiResponse[CharacterResponse].ok(
        await service.create(current_user.id, request)
    )


@router.get("", response_model=ApiResponse[CharacterPageResponse])
async def list_characters(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[CharacterService, Depends(get_character_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> ApiResponse[CharacterPageResponse]:
    return ApiResponse[CharacterPageResponse].ok(
        await service.list_for_user(current_user.id, limit=limit, cursor=cursor)
    )


@router.get("/{character_id}", response_model=ApiResponse[CharacterResponse])
async def get_character(
    character_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> ApiResponse[CharacterResponse]:
    return ApiResponse[CharacterResponse].ok(
        await service.get(current_user.id, character_id)
    )


@router.patch("/{character_id}", response_model=ApiResponse[CharacterResponse])
async def update_character(
    character_id: UUID,
    request: CharacterUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> ApiResponse[CharacterResponse]:
    return ApiResponse[CharacterResponse].ok(
        await service.update(current_user.id, character_id, request)
    )


@router.delete(
    "/{character_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def archive_character(
    character_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> Response:
    await service.archive(current_user.id, character_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
