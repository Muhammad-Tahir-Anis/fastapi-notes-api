from tests.helpers import (  # isort: skip  (must run before the app is imported)
    TEST_DATABASE_URL,
    TEST_DB_NAME,
    drop_database,
    recreate_database,
)

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def engine():
    await recreate_database(TEST_DB_NAME)
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    await drop_database(TEST_DB_NAME)


@pytest_asyncio.fixture
async def client(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users RESTART IDENTITY CASCADE"))


async def register_and_login(client: AsyncClient, email: str, password: str = "secret123") -> dict:
    """Create a user and return Authorization headers for them."""
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201
    response = await client.post(
        "/api/v1/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest_asyncio.fixture
async def auth_headers(client):
    return await register_and_login(client, "alice@example.com")


@pytest_asyncio.fixture
async def other_headers(client):
    return await register_and_login(client, "bob@example.com")
