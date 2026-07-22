from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import get_current_user
from app.domains.chat.dependencies import get_chat_application_service
from app.domains.chat.service import ChatApplicationService
from app.domains.messages.schemas import ChatExchangeResponse, MessageSendRequest
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/conversations", tags=["Chat"])


@router.post(
    "/{conversation_id}/messages",
    response_model=ApiResponse[ChatExchangeResponse],
)
async def send_message(
    conversation_id: UUID,
    request: MessageSendRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[
        ChatApplicationService,
        Depends(get_chat_application_service),
    ],
) -> ApiResponse[ChatExchangeResponse]:
    return ApiResponse[ChatExchangeResponse].ok(
        await service.send_message(current_user.id, conversation_id, request)
    )


@router.post(
    "/{conversation_id}/messages/stream",
    response_class=StreamingResponse,
)
async def stream_message(
    conversation_id: UUID,
    request: MessageSendRequest,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    service: Annotated[
        ChatApplicationService,
        Depends(get_chat_application_service),
    ],
) -> StreamingResponse:
    prepared = await service.start_stream(current_user.id, conversation_id, request)
    return StreamingResponse(
        prepared.events,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
