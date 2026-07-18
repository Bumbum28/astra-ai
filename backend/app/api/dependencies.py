from fastapi import Request

from app.repositories.health_repository import (
    DatabaseHealthRepository,
    RedisHealthRepository,
)
from app.services.health_service import HealthService


def get_health_service(request: Request) -> HealthService:
    settings = request.app.state.settings
    return HealthService(
        database_repository=DatabaseHealthRepository(request.app.state.db_engine),
        redis_repository=RedisHealthRepository(request.app.state.redis),
        service_name=settings.APP_NAME,
        service_version=settings.APP_VERSION,
    )
