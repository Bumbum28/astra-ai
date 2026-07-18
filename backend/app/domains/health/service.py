import asyncio
from datetime import UTC, datetime
from time import perf_counter

from app.domains.health.repository import HealthCheckRepository
from app.domains.health.schemas import DependencyHealth, ReadinessResponse


class HealthService:
    def __init__(
        self,
        database_repository: HealthCheckRepository,
        redis_repository: HealthCheckRepository,
        service_name: str,
        service_version: str,
    ) -> None:
        self._database_repository = database_repository
        self._redis_repository = redis_repository
        self._service_name = service_name
        self._service_version = service_version

    async def readiness(self) -> ReadinessResponse:
        """Return aggregated PostgreSQL and Redis readiness state."""
        database, redis = await asyncio.gather(
            self._check_dependency(self._database_repository),
            self._check_dependency(self._redis_repository),
        )
        checks = {"postgres": database, "redis": redis}
        is_ready = all(check.status == "up" for check in checks.values())
        return ReadinessResponse(
            status="ready" if is_ready else "not_ready",
            service=self._service_name,
            version=self._service_version,
            timestamp=datetime.now(UTC),
            checks=checks,
        )

    @staticmethod
    async def _check_dependency(
        repository: HealthCheckRepository,
    ) -> DependencyHealth:
        started_at = perf_counter()
        try:
            is_up = await repository.ping()
            latency_ms = round((perf_counter() - started_at) * 1000, 2)
            if is_up:
                return DependencyHealth(status="up", latency_ms=latency_ms)
            return DependencyHealth(
                status="down",
                latency_ms=latency_ms,
                detail="Dependency returned an unhealthy response.",
            )
        except Exception as exc:
            return DependencyHealth(
                status="down",
                latency_ms=round((perf_counter() - started_at) * 1000, 2),
                detail=type(exc).__name__,
            )
