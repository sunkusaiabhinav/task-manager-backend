"""
Pytest fixtures shared across all test files.

Key fixture: `client`
  - Creates a fresh in-memory SQLite database for each test
  - Overrides the get_db dependency so tests never touch the real database
  - Returns an AsyncClient that can make real HTTP requests to the FastAPI app
"""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.session import Base, get_db
from app.main import app

# ── In-memory test database ───────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create a fresh async engine with in-memory SQLite for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables and dispose engine after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """
    Provide a database session backed by the in-memory engine.
    Each test gets its own isolated session and schema.
    """
    session_factory = async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """
    Provide an AsyncClient wired to the FastAPI app with the test database.

    - Overrides the get_db dependency → app uses in-memory test database
    - Real database is never touched during tests
    - Each test function starts with a clean slate
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
