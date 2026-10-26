"""Test database setup. Import this module before importing `app`.

It points the whole app at a separate test database, so the dev database is
never touched by the test suite.
"""

import os

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

_dev_url = make_url(str(get_settings().database_url))

TEST_DB_NAME = f"{_dev_url.database}_test"
TEST_DATABASE_URL = _dev_url.set(database=TEST_DB_NAME).render_as_string(hide_password=False)
ADMIN_URL = _dev_url.set(database="postgres").render_as_string(hide_password=False)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
get_settings.cache_clear()


def url_for(database: str) -> str:
    return make_url(TEST_DATABASE_URL).set(database=database).render_as_string(hide_password=False)


async def recreate_database(name: str) -> None:
    await drop_database(name)
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await admin.dispose()


async def drop_database(name: str) -> None:
    admin = create_async_engine(ADMIN_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    await admin.dispose()
