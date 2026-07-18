from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import create_database_engine, create_session_factory
from app.core.redis import create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and release process-wide infrastructure resources."""

    settings = get_settings()
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    redis_client = create_redis_client(settings)

    app.state.settings = settings
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.redis = redis_client

    try:
        yield
    finally:
        await redis_client.aclose()
        await engine.dispose()
