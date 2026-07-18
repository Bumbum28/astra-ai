from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.exceptions import AuthenticationException
from app.core.config import AppConfig, get_config
from app.core.unit_of_work import UnitOfWorkFactory, get_uow_factory
from app.domains.auth.schemas import DeviceContext
from app.domains.auth.security import PasswordHasher, TokenService
from app.domains.auth.service import AuthService
from app.domains.users.schemas import UserResponse
from app.domains.users.service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_password_hasher(
    config: Annotated[AppConfig, Depends(get_config)],
) -> PasswordHasher:
    return PasswordHasher(
        rounds=config.password_bcrypt_rounds,
        minimum_length=config.password_min_length,
    )


def get_token_service(
    config: Annotated[AppConfig, Depends(get_config)],
) -> TokenService:
    return TokenService(config)


def get_auth_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
    password_hasher: Annotated[PasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    config: Annotated[AppConfig, Depends(get_config)],
) -> AuthService:
    return AuthService(uow_factory, password_hasher, token_service, config)


def get_user_service(
    uow_factory: Annotated[UnitOfWorkFactory, Depends(get_uow_factory)],
) -> UserService:
    return UserService(uow_factory)


def get_device_context(request: Request) -> DeviceContext:
    forwarded_for = request.headers.get("x-forwarded-for")
    ip_address = (
        forwarded_for.split(",", maxsplit=1)[0].strip()
        if forwarded_for
        else request.client.host if request.client else None
    )
    return DeviceContext(
        user_agent=request.headers.get("user-agent"),
        ip_address=ip_address,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    token_service: Annotated[TokenService, Depends(get_token_service)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserResponse:
    if credentials is None:
        raise AuthenticationException("Bearer access token is required.")
    claims = token_service.decode(credentials.credentials, expected_type="access")
    user = await user_service.get_user(claims.subject)
    if not user.is_active:
        raise AuthenticationException("User account is inactive.")
    return user
