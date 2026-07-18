import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import bcrypt
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AuthenticationException, ValidationException
from app.core.config import AppConfig
from app.domains.auth.schemas import TokenClaims


class PasswordHasher:
    def __init__(self, rounds: int, minimum_length: int) -> None:
        self._rounds = rounds
        self._minimum_length = minimum_length

    def validate(self, password: str) -> None:
        encoded = password.encode("utf-8")
        if len(password) < self._minimum_length:
            raise ValidationException(
                f"Password must be at least {self._minimum_length} characters."
            )
        if len(encoded) > 72:
            raise ValidationException(
                "Password must not exceed 72 UTF-8 bytes when bcrypt is used."
            )

    def hash(self, password: str) -> str:
        self.validate(password)
        salt = bcrypt.gensalt(rounds=self._rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify(password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False


class TokenService:
    def __init__(self, config: AppConfig) -> None:
        self._secret = config.jwt_secret_key.get_secret_value()
        self._algorithm = config.jwt_algorithm
        self._access_minutes = config.access_token_expire_minutes
        self._refresh_days = config.refresh_token_expire_days

    @property
    def access_expires_in(self) -> int:
        return self._access_minutes * 60

    @property
    def refresh_expires_in(self) -> int:
        return self._refresh_days * 24 * 60 * 60

    def create_access_token(self, user_id: UUID) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._access_minutes)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": expires_at,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        user_id: UUID,
        session_id: UUID,
        family_id: UUID,
        jti: UUID,
        expires_at: datetime,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(jti),
            "session_id": str(session_id),
            "family_id": str(family_id),
            "iat": now,
            "exp": expires_at,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str, expected_type: str) -> TokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": ["sub", "type", "jti", "iat", "exp"]},
            )
        except ExpiredSignatureError as exc:
            raise AuthenticationException(
                "Token has expired.",
                code=ErrorCode.AUTH_TOKEN_EXPIRED,
            ) from exc
        except (InvalidTokenError, ValueError, TypeError) as exc:
            raise AuthenticationException(
                "Token is invalid.",
                code=ErrorCode.AUTH_INVALID_TOKEN,
            ) from exc

        if payload.get("type") != expected_type:
            raise AuthenticationException(
                "Token type is invalid.",
                code=ErrorCode.AUTH_INVALID_TOKEN,
            )

        try:
            return TokenClaims(
                subject=UUID(payload["sub"]),
                token_type=payload["type"],
                jti=UUID(payload["jti"]),
                expires_at=int(payload["exp"]),
                session_id=(
                    UUID(payload["session_id"]) if payload.get("session_id") else None
                ),
                family_id=(
                    UUID(payload["family_id"]) if payload.get("family_id") else None
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthenticationException(
                "Token claims are invalid.",
                code=ErrorCode.AUTH_INVALID_TOKEN,
            ) from exc

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def token_hash_matches(token: str, expected_hash: str) -> bool:
        return hmac.compare_digest(TokenService.hash_token(token), expected_hash)
