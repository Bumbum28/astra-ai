import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authentication_flow_with_rotation_and_logout() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        register = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "astra_user",
                "password": "secure-password",
                "device_name": "integration-test",
            },
        )
        assert register.status_code == 201
        registered_data = register.json()["data"]
        access_token = registered_data["tokens"]["access_token"]
        refresh_token = registered_data["tokens"]["refresh_token"]
        assert "password" not in register.text

        duplicate = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "another_user",
                "password": "secure-password",
            },
        )
        assert duplicate.status_code == 409

        failed_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrong-password"},
        )
        assert failed_login.status_code == 401

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me.status_code == 200
        assert me.json()["data"]["email"] == "user@example.com"

        rotated = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert rotated.status_code == 200
        new_refresh_token = rotated.json()["data"]["tokens"]["refresh_token"]
        assert new_refresh_token != refresh_token

        reused = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert reused.status_code == 401
        assert reused.json()["error"]["code"] == "AUTH_TOKEN_REUSE_DETECTED"

        family_revoked = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": new_refresh_token},
        )
        assert family_revoked.status_code == 401

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "secure-password"},
        )
        assert login.status_code == 200
        login_data = login.json()["data"]

        logout = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": login_data["tokens"]["refresh_token"]},
        )
        assert logout.status_code == 200

        logout_all = await client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {login_data['tokens']['access_token']}"},
        )
        assert logout_all.status_code == 200
