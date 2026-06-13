import json
import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
from app.database import CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS
from app.seed import seed_if_empty

@pytest_asyncio.fixture
async def seeded_db(tmp_path):
    lesson_dir = tmp_path / "lessons" / "unit1"
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "lesson01.json").write_text(json.dumps({
        "unit": 1, "lesson": 1, "title": "Test",
        "cards": [
            {"type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel a"}
        ]
    }), encoding="utf-8")
    db_path = tmp_path / "progress.db"
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()
    return tmp_path

async def test_seed_inserts_cards(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.seed.app.database.get_db_path", lambda: seeded_db / "progress.db")
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
    assert count == 1

async def test_seed_is_idempotent(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.seed.app.database.get_db_path", lambda: seeded_db / "progress.db")
    await seed_if_empty()
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
    assert count == 1
