import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

from app.database import CREATE_USERS, CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS, get_db

@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.execute("INSERT INTO users (name) VALUES ('Tester')")
        await db.commit()
        yield db

@pytest_asyncio.fixture
async def client(tmp_path):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as setup_db:
        await setup_db.execute(CREATE_USERS)
        await setup_db.execute(CREATE_CARDS)
        await setup_db.execute(CREATE_PROGRESS)
        await setup_db.execute(CREATE_LESSONS)
        await setup_db.execute("INSERT INTO users (name) VALUES ('Tester')")
        await setup_db.commit()

    async def override_get_db():
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
