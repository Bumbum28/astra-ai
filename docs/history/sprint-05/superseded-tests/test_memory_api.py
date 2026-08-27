import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manual_memory_crud_and_conversation_snapshot() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "memory@example.com",
                "username": "memory_user",
                "password": "secure-password",
            },
        )
        assert register.status_code == 201
        token = register.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        conversation = await client.post(
            "/api/v1/conversations",
            headers=headers,
            json={"provider": "ollama", "model": "roleplay-engine"},
        )
        assert conversation.status_code == 201
        conversation_id = conversation.json()["data"]["id"]

        created = await client.post(
            "/api/v1/memories",
            headers=headers,
            json={
                "scope": "conversation",
                "kind": "event",
                "conversation_id": conversation_id,
                "content": "Hai người đã tìm thấy ngọn hải đăng.",
                "importance": 0.9,
            },
        )
        assert created.status_code == 201
        memory_id = created.json()["data"]["id"]

        snapshot = await client.get(
            f"/api/v1/conversations/{conversation_id}/memory",
            headers=headers,
        )
        assert snapshot.status_code == 200
        memories = snapshot.json()["data"]["memories"]
        assert len(memories) == 1
        assert memories[0]["id"] == memory_id

        updated = await client.patch(
            f"/api/v1/memories/{memory_id}",
            headers=headers,
            json={"content": "Ngọn hải đăng nằm ở phía tây bắc."},
        )
        assert updated.status_code == 200
        assert "tây bắc" in updated.json()["data"]["content"]

        archived = await client.delete(
            f"/api/v1/memories/{memory_id}",
            headers=headers,
        )
        assert archived.status_code == 204

        listed = await client.get(
            "/api/v1/memories?include_archived=true",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["items"][0]["status"] == "archived"
