from typing import Protocol

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class HealthCheckRepository(Protocol):
    async def ping(self) -> bool:
        """Return True when the dependency is reachable."""


class DatabaseHealthRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def ping(self) -> bool:
        async with self._engine.connect() as connection:
            result = await connection.execute(text("SELECT 1"))
            return result.scalar_one() == 1


class RedisHealthRepository:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def ping(self) -> bool:
        return bool(await self._client.ping())
