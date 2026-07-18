import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import AppConfig
from app.main import create_app


async def _preflight(origin: str, *, origin_regex: str | None) -> Response:
    application = create_app(
        AppConfig(
            CORS_ORIGINS=["http://localhost:8080"],
            CORS_ORIGIN_REGEX=origin_regex,
            CORS_ALLOW_PRIVATE_NETWORK=True,
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=application),
        base_url="http://test",
    ) as client:
        return await client.options(
            "/api/v1/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
                "Access-Control-Request-Private-Network": "true",
            },
        )


@pytest.mark.asyncio
async def test_flutter_web_fixed_port_preflight_is_allowed() -> None:
    response = await _preflight(
        "http://localhost:8080",
        origin_regex=None,
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:8080")


@pytest.mark.asyncio
async def test_flutter_web_random_development_port_preflight_is_allowed() -> None:
    response = await _preflight(
        "http://localhost:62652",
        origin_regex=r"https?://(localhost|127[.]0[.]0[.]1)(:[0-9]+)?",
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:62652")


@pytest.mark.asyncio
async def test_untrusted_origin_is_rejected() -> None:
    response = await _preflight(
        "https://example.invalid",
        origin_regex=r"https?://(localhost|127[.]0[.]0[.]1)(:[0-9]+)?",
    )

    assert response.status_code == 400
