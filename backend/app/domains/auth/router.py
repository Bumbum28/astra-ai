from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.common.responses import ApiResponse
from app.domains.auth.dependencies import (
    get_auth_service,
    get_current_user,
    get_device_context,
)
from app.domains.auth.schemas import (
    AuthResponse,
    DeviceContext,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.domains.auth.service import AuthService
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[AuthResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    device_context: Annotated[DeviceContext, Depends(get_device_context)],
) -> ApiResponse[AuthResponse]:
    context = DeviceContext(
        device_name=request.device_name,
        user_agent=device_context.user_agent,
        ip_address=device_context.ip_address,
    )
    return ApiResponse[AuthResponse].ok(await auth_service.register(request, context))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    device_context: Annotated[DeviceContext, Depends(get_device_context)],
) -> ApiResponse[AuthResponse]:
    context = DeviceContext(
        device_name=request.device_name,
        user_agent=device_context.user_agent,
        ip_address=device_context.ip_address,
    )
    return ApiResponse[AuthResponse].ok(await auth_service.login(request, context))


@router.post("/refresh", response_model=ApiResponse[AuthResponse])
async def refresh(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    device_context: Annotated[DeviceContext, Depends(get_device_context)],
) -> ApiResponse[AuthResponse]:
    context = DeviceContext(
        device_name=request.device_name,
        user_agent=device_context.user_agent,
        ip_address=device_context.ip_address,
    )
    return ApiResponse[AuthResponse].ok(
        await auth_service.refresh_tokens(request.refresh_token, context)
    )


@router.post("/logout", response_model=ApiResponse[dict[str, bool]])
async def logout(
    request: LogoutRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[dict[str, bool]]:
    await auth_service.logout(request.refresh_token)
    return ApiResponse[dict[str, bool]].ok({"logged_out": True})


@router.post("/logout-all", response_model=ApiResponse[dict[str, int]])
async def logout_all(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> ApiResponse[dict[str, int]]:
    revoked_count = await auth_service.logout_all(current_user.id)
    return ApiResponse[dict[str, int]].ok({"revoked_sessions": revoked_count})


@router.get("/me", response_model=ApiResponse[UserResponse])
async def me(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
) -> ApiResponse[UserResponse]:
    return ApiResponse[UserResponse].ok(current_user)
