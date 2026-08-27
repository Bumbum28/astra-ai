import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_character_persona_conversation_and_relationship_flow() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "roleplay@example.com",
                "username": "roleplay_user",
                "password": "secure-password",
            },
        )
        assert register.status_code == 201
        access_token = register.json()["data"]["tokens"]["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        character = await client.post(
            "/api/v1/characters",
            headers=headers,
            json={
                "name": "Kael",
                "personality": "Kiềm chế và bảo vệ.",
                "speaking_style": "Chậm rãi.",
                "provider": "ollama",
                "model": "roleplay-engine",
            },
        )
        assert character.status_code == 201
        character_id = character.json()["data"]["id"]

        revised = await client.patch(
            f"/api/v1/characters/{character_id}",
            headers=headers,
            json={"scenario": "Một thế giới băng giá."},
        )
        assert revised.status_code == 200
        assert revised.json()["data"]["current_version"] == 2

        persona = await client.post(
            "/api/v1/personas",
            headers=headers,
            json={"name": "Ari", "pronouns": "hắn"},
        )
        assert persona.status_code == 201
        persona_id = persona.json()["data"]["id"]

        conversation = await client.post(
            "/api/v1/conversations",
            headers=headers,
            json={
                "character_id": character_id,
                "persona_id": persona_id,
            },
        )
        assert conversation.status_code == 201
        conversation_data = conversation.json()["data"]
        assert conversation_data["character_id"] == character_id
        assert conversation_data["character_version_id"] is not None
        assert conversation_data["persona_id"] == persona_id
        assert conversation_data["provider"] == "ollama"
        conversation_id = conversation_data["id"]

        relationship = await client.get(
            f"/api/v1/conversations/{conversation_id}/relationship",
            headers=headers,
        )
        assert relationship.status_code == 200
        assert relationship.json()["data"]["level"] == "l0"

        updated = await client.patch(
            f"/api/v1/conversations/{conversation_id}/relationship",
            headers=headers,
            json={
                "level": "l3",
                "affection_score": 40,
                "status": "Mập mờ",
                "reason": "Bắt đầu tin tưởng nhau.",
            },
        )
        assert updated.status_code == 200
        assert updated.json()["data"]["level"] == "l3"

        history = await client.get(
            f"/api/v1/conversations/{conversation_id}/relationship/events",
            headers=headers,
        )
        assert history.status_code == 200
        assert history.json()["data"]["items"][0]["score_delta"] == 40
