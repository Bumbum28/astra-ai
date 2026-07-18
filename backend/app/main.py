from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.common.exceptions import AppException
from app.common.exceptions.handlers import global_exception_handler
from app.common.responses import ApiResponse
from app.core.config import get_config
from app.core.lifespan import lifespan
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    config = get_config()
    configure_logging(config.debug)
    application = FastAPI(
        title=config.app_name,
        version=config.app_version,
        debug=config.debug,
        lifespan=lifespan,
        docs_url=None if config.app_env == "production" else "/docs",
        redoc_url=None if config.app_env == "production" else "/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for exception_type in (
        AppException,
        RequestValidationError,
        HTTPException,
        Exception,
    ):
        application.add_exception_handler(exception_type, global_exception_handler)
    application.include_router(api_router)

    @application.get("/", response_model=ApiResponse[dict[str, str]], tags=["Root"])
    async def root() -> ApiResponse[dict[str, str]]:
        return ApiResponse[dict[str, str]].ok(
            {
                "service": config.app_name,
                "version": config.app_version,
                "docs": "/docs" if config.app_env != "production" else "disabled",
            }
        )

    return application


app = create_app()
