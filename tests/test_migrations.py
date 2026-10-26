import asyncio
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.helpers import TEST_DB_NAME, drop_database, recreate_database, url_for

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_DB = f"{TEST_DB_NAME}_migrations"


def run_alembic(url: str, *args: str) -> None:
    env = {**os.environ, "DATABASE_URL": url}
    subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


async def table_names(url: str) -> set[str]:
    engine = create_async_engine(url, poolclass=NullPool)
    async with engine.connect() as conn:
        names = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    await engine.dispose()
    return names


async def test_migrations_build_schema_from_scratch_and_roll_back():
    url = url_for(MIGRATION_DB)
    await recreate_database(MIGRATION_DB)
    try:
        await asyncio.to_thread(run_alembic, url, "upgrade", "head")
        assert {"users", "notes", "alembic_version"} <= await table_names(url)

        await asyncio.to_thread(run_alembic, url, "downgrade", "base")
        assert await table_names(url) == {"alembic_version"}
    finally:
        await drop_database(MIGRATION_DB)
