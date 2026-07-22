import os

import pytest
from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.core.database import AsyncSessionFactory


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for integration tests.")
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
async def clean_database(migrated_database: None) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(
            text(
                "TRUNCATE memory_tasks, conversation_summaries, memories, "
                "relationship_events, relationships, messages, conversations, "
                "character_versions, characters, persona_versions, "
                "personas, refresh_sessions, users RESTART IDENTITY CASCADE"
            )
        )
        await session.commit()
