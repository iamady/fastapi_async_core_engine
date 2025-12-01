import pytest
import asyncio
from typing import Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db, AsyncSessionLocal
from app.main import app


# In-memory SQLite engine for testing
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    poolclass=StaticPool
)

# Create async session factory for testing
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def override_get_db():
    """Override get_db dependency for testing"""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# Override the dependency in the FastAPI app
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def test_customer_data():
    """Sample customer data for testing."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com"
    }


@pytest.fixture
async def test_product_data():
    """Sample product data for testing."""
    return {
        "name": "Test Product",
        "category": "Electronics",
        "price": 99.99,
        "description": "A test product"
    }


@pytest.fixture
async def test_order_data():
    """Sample order data for testing."""
    return {
        "customer_id": 1,
        "product_id": 1,
        "quantity": 2
    }
