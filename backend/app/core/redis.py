from redis.asyncio import Redis

from app.core.config import Settings


def create_redis_client(settings: Settings) -> Redis:
    """Create the shared asynchronous Redis client."""

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=settings.REDIS_SOCKET_TIMEOUT,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        health_check_interval=30,
    )
