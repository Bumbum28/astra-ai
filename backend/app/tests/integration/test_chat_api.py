from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.llm.chat.service import ChatService as LLMChatService
from app.llm.contracts import LLMChunk, LLMRequest, LLMResponse
from app.llm.dependencies import get_llm_chat_service
from app.main import app


class IntegrationFakeLLMService(LLMChatService):
    def __init__(self) -> None:
        pass

    async def generate(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> LLMResponse:
        return LLMResponse(
            content="Phản hồi integration.",
            provider=provider_name,
            model=request.model or "fake-model",
        )

    def stream(
        self,
        provider_name: str,
        request: LLMRequest,
    ) -> AsyncIterator[LLMChunk]:
        async def iterator() -> AsyncIterator[LLMChunk]:
            for text in ("Phản ", "hồi stream."):
                yield LLMChunk(
                    content=text,
                    provider=provider_name,
                    model=request.model or "fake-model",
                )

        return iterator()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_history_and_streaming_chat() -> None:
    app.dependency_overrides[get_llm_chat_service] = IntegrationFakeLLMService
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            register = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "chat@example.com",
                    "username": "chat_user",
                    "password": "secure-password",
                },
            )
            assert register.status_code == 201
            access_token = register.json()["data"]["tokens"]["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}

            created = await client.post(
                "/api/v1/conversations",
                json={"provider": "ollama", "model": "roleplay-engine"},
                headers=headers,
            )
            assert created.status_code == 201
            conversation_id = created.json()["data"]["id"]

            streamed = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages/stream",
                json={
                    "content": "Xin chào",
                    "client_message_id": "00000000-0000-4000-8000-000000000001",
                },
                headers=headers,
            )
            assert streamed.status_code == 200
            assert "event: message.created" in streamed.text
            assert "event: message.delta" in streamed.text
            assert "event: message.completed" in streamed.text

            messages = await client.get(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=headers,
            )
            assert messages.status_code == 200
            items = messages.json()["data"]["items"]
            assert [item["role"] for item in items] == ["user", "assistant"]
            assert items[-1]["content"] == "Phản hồi stream."

            conversations = await client.get(
                "/api/v1/conversations",
                headers=headers,
            )
            assert conversations.status_code == 200
            assert conversations.json()["data"]["items"][0]["title"] == "Xin chào"

            agent_streamed = await client.post(
                f"/api/v1/conversations/{conversation_id}/messages/stream",
                json={
                    "content": "Tóm tắt ngắn cuộc trò chuyện này",
                    "client_message_id": "00000000-0000-4000-8000-000000000002",
                    "execution_mode": "agent",
                },
                headers=headers,
            )
            assert agent_streamed.status_code == 200
            assert '"execution_mode":"agent"' in agent_streamed.text.replace(" ", "")

            agent_runs = await client.get("/api/v1/agent-runs", headers=headers)
            assert agent_runs.status_code == 200
            runs = agent_runs.json()["data"]["items"]
            assert len(runs) == 1
            assert runs[0]["conversation_id"] == conversation_id
            assert runs[0]["status"] == "completed"

            run_detail = await client.get(
                f"/api/v1/agent-runs/{runs[0]['id']}/steps",
                headers=headers,
            )
            assert run_detail.status_code == 200
            steps = run_detail.json()["data"]["items"]
            assert [step["kind"] for step in steps] == ["model"]
    finally:
        app.dependency_overrides.pop(get_llm_chat_service, None)
