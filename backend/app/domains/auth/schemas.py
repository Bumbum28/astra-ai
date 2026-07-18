from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.domains.users.schemas import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    device_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    device_name: str | None = Field(default=None, max_length=120)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=20)
    device_name: str | None = Field(default=None, max_length=120)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_in: int
    refresh_expires_in: int


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPairResponse


@dataclass(frozen=True, slots=True)
class DeviceContext:
    device_name: str | None = None
    user_agent: str | None = None
    ip_address: str | None = None


@dataclass(frozen=True, slots=True)
class TokenClaims:
    subject: UUID
    token_type: str
    jti: UUID
    expires_at: int
    session_id: UUID | None = None
    family_id: UUID | None = None
