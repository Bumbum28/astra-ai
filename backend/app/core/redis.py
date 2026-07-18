from redis.asyncio import Redis

from app.core.config import get_config

config = get_config()
redis_client: Redis = Redis.from_url(
    config.redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_timeout=config.redis_socket_timeout,
)
