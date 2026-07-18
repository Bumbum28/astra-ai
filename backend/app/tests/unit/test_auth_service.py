import pytest

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AuthenticationException
from app.core.config import AppConfig
from app.domains.auth.schemas import DeviceContext, LoginRequest, RegisterRequest
from app.domains.auth.security import PasswordHasher, TokenService
from app.domains.auth.service import AuthService
from app.tests.unit.fakes import FakeUnitOfWorkFactory


def build_service() -> tuple[AuthService, FakeUnitOfWorkFactory]:
    config = AppConfig(PASSWORD_BCRYPT_ROUNDS=10)
    uow_factory = FakeUnitOfWorkFactory()
    service = AuthService(
        uow_factory,
        PasswordHasher(rounds=10, minimum_length=8),
        TokenService(config),
        config,
    )
    return service, uow_factory


@pytest.mark.asyncio
async def test_register_login_refresh_and_reuse_detection() -> None:
    service, uow_factory = build_service()
    registered = await service.register(
        RegisterRequest(
            email="User@Example.com",
            username="Astra_User",
            password="secure-password",
        ),
        DeviceContext(device_name="desktop"),
    )
    assert registered.user.email == "user@example.com"
    assert registered.user.username == "astra_user"
    assert len(uow_factory.sessions.items) == 1

    logged_in = await service.login(
        LoginRequest(email="user@example.com", password="secure-password"),
        DeviceContext(device_name="phone"),
    )
    assert logged_in.tokens.refresh_token != registered.tokens.refresh_token
    assert len(uow_factory.sessions.items) == 2

    rotated = await service.refresh_tokens(
        logged_in.tokens.refresh_token,
        DeviceContext(device_name="phone"),
    )
    assert rotated.tokens.refresh_token != logged_in.tokens.refresh_token

    with pytest.raises(AuthenticationException) as exc_info:
        await service.refresh_tokens(
            logged_in.tokens.refresh_token,
            DeviceContext(device_name="phone"),
        )
    assert exc_info.value.code == ErrorCode.AUTH_TOKEN_REUSE_DETECTED


@pytest.mark.asyncio
async def test_logout_all_revokes_sessions() -> None:
    service, uow_factory = build_service()
    result = await service.register(
        RegisterRequest(
            email="user@example.com",
            username="astra_user",
            password="secure-password",
        ),
        DeviceContext(),
    )
    count = await service.logout_all(result.user.id)
    assert count == 1
    assert all(item.is_revoked for item in uow_factory.sessions.items.values())
