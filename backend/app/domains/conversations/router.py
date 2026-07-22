from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.conversations.dependencies import get_conversation_service
from app.domains.conversations.schemas import (
    ConversationCreateRequest,
    ConversationPageResponse,
    ConversationResponse,
    ConversationUpdateRequest,
)
from app.domains.conversations.service import ConversationService
from app.domains.messages.schemas import MessagePageResponse
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post(
    "",
    response_model=ApiResponse[ConversationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ApiResponse[ConversationResponse]:
    return ApiResponse[ConversationResponse].ok(
        await service.create(current_user.id, request)
    )


@router.get("", response_model=ApiResponse[ConversationPageResponse])
async def list_conversations(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
    cursor: str | None = None,
) -> ApiResponse[ConversationPageResponse]:
    return ApiResponse[ConversationPageResponse].ok(
        await service.list_for_user(current_user.id, limit=limit, cursor=cursor)
    )


@router.get("/{conversation_id}", response_model=ApiResponse[ConversationResponse])
async def get_conversation(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ApiResponse[ConversationResponse]:
    return ApiResponse[ConversationResponse].ok(
        await service.get(current_user.id, conversation_id)
    )


@router.patch(
    "/{conversation_id}", response_model=ApiResponse[ConversationResponse]
)
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdateRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> ApiResponse[ConversationResponse]:
    return ApiResponse[ConversationResponse].ok(
        await service.update(current_user.id, conversation_id, request)
    )


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def archive_conversation(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
) -> Response:
    await service.archive(current_user.id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{conversation_id}/messages",
    response_model=ApiResponse[MessagePageResponse],
)
async def list_messages(
    conversation_id: UUID,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: str | None = None,
) -> ApiResponse[MessagePageResponse]:
    return ApiResponse[MessagePageResponse].ok(
        await service.list_messages(
            current_user.id,
            conversation_id,
            limit=limit,
            cursor=cursor,
        )
    )
