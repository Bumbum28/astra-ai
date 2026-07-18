from inspect import signature
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.common.exceptions import AppException
from app.common.exceptions.handlers import global_exception_handler
from app.common.responses import ApiResponse
from app.core.config import AppConfig, get_config
from app.core.lifespan import lifespan
from app.core.logging import configure_logging


def _cors_options(config: AppConfig) -> dict[str, Any]:
    options: dict[str, Any] = {
        "allow_origins": config.cors_origins,
        "allow_origin_regex": config.cors_origin_regex,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }

    # Newer Starlette versions validate Private Network Access preflights.
    # Keep compatibility with older versions that do not expose this option.
    if "allow_private_network" in signature(CORSMiddleware.__init__).parameters:
        options["allow_private_network"] = config.cors_allow_private_network

    return options


def create_app(config: AppConfig | None = None) -> FastAPI:
    resolved_config = config or get_config()
    configure_logging(resolved_config.debug)
    application = FastAPI(
        title=resolved_config.app_name,
        version=resolved_config.app_version,
        debug=resolved_config.debug,
        lifespan=lifespan,
        docs_url=None if resolved_config.app_env == "production" else "/docs",
        redoc_url=None if resolved_config.app_env == "production" else "/redoc",
    )
    application.add_middleware(
        CORSMiddleware,
        **_cors_options(resolved_config),
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
                "service": resolved_config.app_name,
                "version": resolved_config.app_version,
                "docs": (
                    "/docs" if resolved_config.app_env != "production" else "disabled"
                ),
            }
        )

    return application


app = create_app()
