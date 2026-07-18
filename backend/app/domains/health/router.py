from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.common.responses import ApiResponse
from app.core.config import AppConfig, get_config
from app.core.database import engine
from app.core.redis import redis_client
from app.domains.health.repository import (
    DatabaseHealthRepository,
    RedisHealthRepository,
)
from app.domains.health.schemas import LivenessResponse, ReadinessResponse
from app.domains.health.service import HealthService

router = APIRouter(prefix="/health", tags=["Health"])


def get_health_service(
    config: Annotated[AppConfig, Depends(get_config)],
) -> HealthService:
    return HealthService(
        DatabaseHealthRepository(engine),
        RedisHealthRepository(redis_client),
        config.app_name,
        config.app_version,
    )


@router.get("/live", response_model=ApiResponse[LivenessResponse])
async def liveness(
    config: Annotated[AppConfig, Depends(get_config)],
) -> ApiResponse[LivenessResponse]:
    return ApiResponse[LivenessResponse].ok(
        LivenessResponse(
            service=config.app_name,
            version=config.app_version,
            environment=config.app_env,
            timestamp=datetime.now(UTC),
        )
    )


@router.get("/ready", response_model=ApiResponse[ReadinessResponse])
async def readiness(
    response: Response,
    health_service: Annotated[HealthService, Depends(get_health_service)],
) -> ApiResponse[ReadinessResponse]:
    result = await health_service.readiness()
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ApiResponse[ReadinessResponse].ok(result)
