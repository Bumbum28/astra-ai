from collections.abc import AsyncIterator

from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_config
from app.models.loader import load_all_models

load_all_models()
config = get_config()

if config.app_env.lower() == "test":
    # pytest-asyncio may create a fresh event loop per async test. AsyncPG
    # connections are bound to the loop that created them, so pooling those
    # connections across tests can raise "Future attached to a different loop".
    engine: AsyncEngine = create_async_engine(
        config.database_url,
        pool_pre_ping=True,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        config.database_url,
        pool_pre_ping=True,
        pool_size=config.database_pool_size,
        max_overflow=config.database_max_overflow,
        pool_timeout=config.database_pool_timeout,
    )

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session
