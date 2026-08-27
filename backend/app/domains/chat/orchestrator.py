from uuid import UUID

from app.domains.chat.service import ChatApplicationService, PreparedChatStream
from app.domains.messages.schemas import (
    ChatExchangeResponse,
    ChatExecutionMode,
    MessageSendRequest,
)


class ChatOrchestrator:
    """Select direct or agent execution without coupling the router to runtimes."""

    def __init__(
        self,
        direct_service: ChatApplicationService,
        agent_service: ChatApplicationService,
    ) -> None:
        self._direct_service = direct_service
        self._agent_service = agent_service

    async def send_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: MessageSendRequest,
    ) -> ChatExchangeResponse:
        service = self._select(request.execution_mode)
        return await service.send_message(user_id, conversation_id, request)

    async def start_stream(
        self,
        user_id: UUID,
        conversation_id: UUID,
        request: MessageSendRequest,
    ) -> PreparedChatStream:
        service = self._select(request.execution_mode)
        return await service.start_stream(user_id, conversation_id, request)

    def _select(self, mode: ChatExecutionMode) -> ChatApplicationService:
        return (
            self._agent_service
            if mode == ChatExecutionMode.AGENT
            else self._direct_service
        )
