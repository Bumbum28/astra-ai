import logging
from http import HTTPStatus

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.constants.error_codes import ErrorCode
from app.common.exceptions import AppException
from app.common.responses import ApiResponse

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, AppException):
        response = ApiResponse[None].fail(
            code=exc.code.value,
            message=exc.message,
            details=exc.details,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(response),
            headers=(
                {"WWW-Authenticate": "Bearer"}
                if exc.status_code == HTTPStatus.UNAUTHORIZED
                else None
            ),
        )

    if isinstance(exc, RequestValidationError):
        response = ApiResponse[None].fail(
            code=ErrorCode.VALIDATION_ERROR.value,
            message="Request validation failed.",
            details=exc.errors(),
        )
        return JSONResponse(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(response),
        )

    if isinstance(exc, HTTPException):
        response = ApiResponse[None].fail(
            code=(
                ErrorCode.NOT_FOUND.value
                if exc.status_code == HTTPStatus.NOT_FOUND
                else ErrorCode.INTERNAL_ERROR.value
            ),
            message=str(exc.detail),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(response),
            headers=exc.headers,
        )

    logger.exception(
        "Unhandled application error",
        extra={"path": request.url.path, "method": request.method},
    )
    response = ApiResponse[None].fail(
        code=ErrorCode.INTERNAL_ERROR.value,
        message="An unexpected error occurred.",
    )
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(response),
    )
