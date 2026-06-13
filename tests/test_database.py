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
    assert {"users", "cards", "progress", "lessons"} <= tables

@pytest.mark.asyncio
async def test_init_db_migration_adds_user_id_to_progress(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.get_db_path", lambda: tmp_path / "test.db")
    # Create old-schema progress table (no user_id)
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        await db.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, avatar_path TEXT, created_at DATETIME NOT NULL DEFAULT (datetime('now')))""")
        await db.execute("""CREATE TABLE cards (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, character TEXT NOT NULL, romaji TEXT NOT NULL, meaning TEXT NOT NULL, unit INTEGER NOT NULL, lesson INTEGER NOT NULL, language TEXT NOT NULL DEFAULT 'japanese', audio_path TEXT)""")
        await db.execute("""CREATE TABLE progress (card_id INTEGER PRIMARY KEY, due_date DATE NOT NULL, interval_days INTEGER NOT NULL DEFAULT 1, ease_factor REAL NOT NULL DEFAULT 2.5, review_count INTEGER NOT NULL DEFAULT 0, last_score INTEGER)""")
        await db.execute("""CREATE TABLE lessons (lesson_id INTEGER NOT NULL, unit INTEGER NOT NULL, completed_at DATETIME, quiz_score TEXT, PRIMARY KEY (lesson_id, unit))""")
        await db.execute("INSERT INTO cards (type,character,romaji,meaning,unit,lesson) VALUES ('hiragana','あ','a','vowel',1,1)")
        await db.execute("INSERT INTO progress (card_id, due_date, interval_days, ease_factor, review_count) VALUES (1, date('now'), 1, 2.5, 0)")
        await db.execute("INSERT INTO lessons (lesson_id, unit, completed_at) VALUES (1, 1, datetime('now'))")
        await db.commit()
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        cursor = await db.execute("PRAGMA table_info(progress)")
        cols = {r[1] for r in await cursor.fetchall()}
        assert "user_id" in cols
        cursor = await db.execute("PRAGMA table_info(lessons)")
        cols = {r[1] for r in await cursor.fetchall()}
        assert "user_id" in cols
        assert "language" in cols
        # Default user was created
        cursor = await db.execute("SELECT name FROM users")
        users = [r[0] for r in await cursor.fetchall()]
        assert "Player 1" in users
