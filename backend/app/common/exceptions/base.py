from http import HTTPStatus
from typing import Any

from app.common.constants.error_codes import ErrorCode


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class AuthenticationException(AppException):
    def __init__(
        self,
        message: str = "Authentication failed.",
        code: ErrorCode = ErrorCode.AUTH_INVALID_CREDENTIALS,
        status_code: int = HTTPStatus.UNAUTHORIZED,
        details: Any | None = None,
    ) -> None:
        super().__init__(code, message, status_code, details)


class AuthorizationException(AppException):
    def __init__(
        self,
        message: str = "You are not allowed to perform this action.",
        code: ErrorCode = ErrorCode.AUTH_FORBIDDEN,
        details: Any | None = None,
    ) -> None:
        super().__init__(code, message, HTTPStatus.FORBIDDEN, details)


class ValidationException(AppException):
    def __init__(
        self,
        message: str = "Request validation failed.",
        details: Any | None = None,
    ) -> None:
        super().__init__(
            ErrorCode.VALIDATION_ERROR,
            message,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            details,
        )


class NotFoundException(AppException):
    def __init__(
        self,
        message: str = "Resource not found.",
        code: ErrorCode = ErrorCode.NOT_FOUND,
    ) -> None:
        super().__init__(code, message, HTTPStatus.NOT_FOUND)


class ConflictException(AppException):
    def __init__(
        self,
        message: str = "Resource conflict.",
        code: ErrorCode = ErrorCode.CONFLICT,
    ) -> None:
        super().__init__(code, message, HTTPStatus.CONFLICT)


class LLMException(AppException):
    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.LLM_PROVIDER_ERROR,
        status_code: int = HTTPStatus.BAD_GATEWAY,
        details: Any | None = None,
    ) -> None:
        super().__init__(code, message, status_code, details)
