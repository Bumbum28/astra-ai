from asyncio import to_thread
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import (
    AuthenticationException,
    ConflictException,
    NotFoundException,
)
from app.core.config import AppConfig
from app.core.unit_of_work import UnitOfWork, UnitOfWorkFactory
from app.domains.auth.model import RefreshSession
from app.domains.auth.schemas import (
    AuthResponse,
    DeviceContext,
    LoginRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.domains.auth.security import PasswordHasher, TokenService
from app.domains.users.model import User
from app.domains.users.schemas import UserResponse
from app.utils.helpers import normalize_email, normalize_username
from app.utils.validators import validate_username


class AuthService:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        config: AppConfig,
    ) -> None:
        self._uow_factory = uow_factory
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._refresh_days = config.refresh_token_expire_days

    async def register(
        self,
        request: RegisterRequest,
        context: DeviceContext,
    ) -> AuthResponse:
        """Create a user and an initial refresh session atomically."""
        email = normalize_email(str(request.email))
        username = normalize_username(request.username)
        validate_username(username)
        password_hash = await to_thread(self._password_hasher.hash, request.password)

        async with self._uow_factory() as uow:
            if await uow.users.get_by_email(email):
                raise ConflictException(
                    "Email is already registered.", ErrorCode.AUTH_EMAIL_EXISTS
                )
            if await uow.users.get_by_username(username):
                raise ConflictException(
                    "Username is already registered.",
                    ErrorCode.AUTH_USERNAME_EXISTS,
                )

            user = User(
                id=uuid4(),
                email=email,
                username=username,
                password_hash=password_hash,
                is_active=True,
                is_verified=False,
            )
            await uow.users.add(user)
            await uow.flush()
            tokens = await self._create_session(uow, user.id, context)
            await uow.flush()
            response = AuthResponse(
                user=UserResponse.model_validate(user),
                tokens=tokens,
            )
            await uow.commit()
            return response

    async def login(
        self,
        request: LoginRequest,
        context: DeviceContext,
    ) -> AuthResponse:
        """Authenticate a user and create an independent device session."""
        email = normalize_email(str(request.email))
        async with self._uow_factory() as uow:
            user = await uow.users.get_by_email(email)
            password_matches = (
                await to_thread(
                    self._password_hasher.verify,
                    request.password,
                    user.password_hash,
                )
                if user is not None
                else False
            )
            if user is None or not password_matches:
                raise AuthenticationException("Email or password is incorrect.")
            if not user.is_active:
                raise AuthenticationException(
                    "User account is inactive.",
                    code=ErrorCode.AUTH_INACTIVE_USER,
                )

            user.last_login_at = datetime.now(UTC)
            tokens = await self._create_session(uow, user.id, context)
            await uow.flush()
            response = AuthResponse(
                user=UserResponse.model_validate(user),
                tokens=tokens,
            )
            await uow.commit()
            return response

    async def refresh_tokens(
        self,
        refresh_token: str,
        context: DeviceContext,
    ) -> AuthResponse:
        """Rotate a refresh token and invalidate the previous session token."""
        claims = self._token_service.decode(refresh_token, expected_type="refresh")
        if claims.session_id is None or claims.family_id is None:
            raise AuthenticationException(
                "Refresh token claims are incomplete.",
                code=ErrorCode.AUTH_INVALID_TOKEN,
            )

        async with self._uow_factory() as uow:
            session = await uow.refresh_sessions.get_by_id(
                claims.session_id, for_update=True
            )
            if session is None:
                raise AuthenticationException(
                    "Refresh session was not found.",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                )

            if session.is_revoked:
                if session.replaced_by_session_id is not None:
                    await uow.refresh_sessions.revoke_family(session.token_family_id)
                    await uow.commit()
                    raise AuthenticationException(
                        "Refresh token reuse was detected. "
                        "The session family was revoked.",
                        code=ErrorCode.AUTH_TOKEN_REUSE_DETECTED,
                    )
                raise AuthenticationException(
                    "Refresh token has been revoked.",
                    code=ErrorCode.AUTH_TOKEN_REVOKED,
                )

            if session.is_expired:
                raise AuthenticationException(
                    "Refresh token has expired.",
                    code=ErrorCode.AUTH_TOKEN_EXPIRED,
                )

            if (
                session.user_id != claims.subject
                or session.token_jti != claims.jti
                or session.token_family_id != claims.family_id
                or not self._token_service.token_hash_matches(
                    refresh_token, session.token_hash
                )
            ):
                await uow.refresh_sessions.revoke_family(session.token_family_id)
                await uow.commit()
                raise AuthenticationException(
                    "Refresh token validation failed.",
                    code=ErrorCode.AUTH_TOKEN_REUSE_DETECTED,
                )

            user = await uow.users.get_by_id(session.user_id)
            if user is None:
                raise NotFoundException("User not found.")
            if not user.is_active:
                raise AuthenticationException(
                    "User account is inactive.",
                    code=ErrorCode.AUTH_INACTIVE_USER,
                )

            new_session_id = uuid4()
            new_jti = uuid4()
            expires_at = datetime.now(UTC) + timedelta(days=self._refresh_days)
            new_refresh_token = self._token_service.create_refresh_token(
                user_id=user.id,
                session_id=new_session_id,
                family_id=session.token_family_id,
                jti=new_jti,
                expires_at=expires_at,
            )
            replacement = RefreshSession(
                id=new_session_id,
                user_id=user.id,
                token_jti=new_jti,
                token_hash=self._token_service.hash_token(new_refresh_token),
                token_family_id=session.token_family_id,
                expires_at=expires_at,
                device_name=context.device_name or session.device_name,
                user_agent=context.user_agent or session.user_agent,
                ip_address=context.ip_address or session.ip_address,
            )
            await uow.refresh_sessions.add(replacement)
            # The replacement must exist before the previous session references it.
            # Without this explicit flush, SQLAlchemy can issue the UPDATE first and
            # violate the self-referential foreign key on replaced_by_session_id.
            await uow.flush()
            session.revoked_at = datetime.now(UTC)
            session.replaced_by_session_id = replacement.id
            response = AuthResponse(
                user=UserResponse.model_validate(user),
                tokens=self._build_token_pair(user.id, new_refresh_token),
            )
            await uow.commit()
            return response

    async def logout(self, refresh_token: str) -> None:
        """Revoke one refresh session; repeated logout remains idempotent."""
        claims = self._token_service.decode(refresh_token, expected_type="refresh")
        if claims.session_id is None:
            raise AuthenticationException(
                "Refresh token claims are incomplete.",
                code=ErrorCode.AUTH_INVALID_TOKEN,
            )

        async with self._uow_factory() as uow:
            session = await uow.refresh_sessions.get_by_id(
                claims.session_id, for_update=True
            )
            if session is None:
                return
            if not self._token_service.token_hash_matches(
                refresh_token, session.token_hash
            ):
                raise AuthenticationException(
                    "Refresh token validation failed.",
                    code=ErrorCode.AUTH_INVALID_TOKEN,
                )
            if session.revoked_at is None:
                session.revoked_at = datetime.now(UTC)
                await uow.commit()

    async def logout_all(self, user_id: UUID) -> int:
        """Revoke every active refresh session owned by a user."""
        async with self._uow_factory() as uow:
            revoked_count = await uow.refresh_sessions.revoke_all_for_user(user_id)
            await uow.commit()
            return revoked_count

    async def _create_session(
        self,
        uow: UnitOfWork,
        user_id: UUID,
        context: DeviceContext,
    ) -> TokenPairResponse:
        session_id = uuid4()
        family_id = uuid4()
        jti = uuid4()
        expires_at = datetime.now(UTC) + timedelta(days=self._refresh_days)
        refresh_token = self._token_service.create_refresh_token(
            user_id=user_id,
            session_id=session_id,
            family_id=family_id,
            jti=jti,
            expires_at=expires_at,
        )
        refresh_session = RefreshSession(
            id=session_id,
            user_id=user_id,
            token_jti=jti,
            token_hash=self._token_service.hash_token(refresh_token),
            token_family_id=family_id,
            expires_at=expires_at,
            device_name=context.device_name,
            user_agent=context.user_agent,
            ip_address=context.ip_address,
        )
        await uow.refresh_sessions.add(refresh_session)
        return self._build_token_pair(user_id, refresh_token)

    def _build_token_pair(self, user_id: UUID, refresh_token: str) -> TokenPairResponse:
        return TokenPairResponse(
            access_token=self._token_service.create_access_token(user_id),
            refresh_token=refresh_token,
            access_expires_in=self._token_service.access_expires_in,
            refresh_expires_in=self._token_service.refresh_expires_in,
        )
