import pytest
import aiosqlite

@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.get_db_path", lambda: tmp_path / "test.db")
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in await cursor.fetchall()}
    # sqlite_sequence is auto-created by AUTOINCREMENT; use subset check
    assert {"cards", "progress", "lessons"} <= tables
