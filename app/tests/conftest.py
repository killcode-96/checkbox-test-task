import os
import uuid
import asyncio

import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database.db import get_db
from app.database import models
from app.schemas.user import UserCreate
from app.services.user import UserService


@pytest_asyncio.fixture(scope="session")
async def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


load_dotenv()

TEST_DATABASE_URL = f"postgresql+asyncpg://{os.getenv("POSTGRES_USER")}:{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


@pytest_asyncio.fixture(loop_scope="session", autouse=True)
async def create_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)


@pytest_asyncio.fixture(loop_scope="session")
async def override_get_db():
    async def _override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(loop_scope="session")
async def client(override_get_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://0.0.0.0:8000") as ac:
        yield ac


@pytest_asyncio.fixture(loop_scope="session")
async def create_test_user():
    test_user_data = UserCreate(
        username=f"test_user{str(uuid.uuid4())}",
        full_name="Test User",
        password="test_password",
    )
    async with TestSessionLocal() as session:
        user_service = UserService(session)
        user = await user_service.create_user(test_user_data)
        yield user


@pytest_asyncio.fixture(loop_scope="session")
async def auth_header(client, create_test_user):
    response = await client.post(
        "/users/signin/",
        json={"username": f"{create_test_user.username}", "password": "test_password"},
    )
    return {
        "Authorization": f"{response.json()['token_type']} {response.json()['access_token']}"
    }


@pytest_asyncio.fixture(loop_scope="session")
async def create_test_receipt(client, create_test_user, auth_header):
    response = await client.post(
        "/receipts/",
        json={
            "products": [
                {"name": "Product 1", "price": 10.0, "quantity": 2},
                {"name": "Product 2", "price": 20.0, "quantity": 1},
            ],
            "payment": {"type": "cash", "amount": 40.0},
        },
        headers=auth_header,
    )
    return response.json()
