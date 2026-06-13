from pathlib import Path
import aiosqlite
from app.config import settings

def get_db_path() -> Path:
    return Path(settings.data_dir) / "progress.db"

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    avatar_path TEXT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
)
"""

CREATE_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    character TEXT NOT NULL,
    romaji TEXT NOT NULL,
    meaning TEXT NOT NULL,
    unit INTEGER NOT NULL,
    lesson INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT 'japanese',
    audio_path TEXT
)
"""

CREATE_PROGRESS = """
CREATE TABLE IF NOT EXISTS progress (
    card_id INTEGER NOT NULL REFERENCES cards(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    due_date DATE NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_score INTEGER,
    PRIMARY KEY (card_id, user_id)
)
"""

CREATE_LESSONS = """
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER NOT NULL,
    unit INTEGER NOT NULL,
    language TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    completed_at DATETIME,
    quiz_score TEXT,
    PRIMARY KEY (lesson_id, unit, language, user_id)
)
"""

async def _ensure_default_user(db) -> int:
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    if (await cursor.fetchone())[0] == 0:
        await db.execute("INSERT INTO users (name) VALUES ('Player 1')")
    cursor = await db.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    return (await cursor.fetchone())[0]

async def _migrate_progress(db) -> None:
    user_id = await _ensure_default_user(db)
    await db.execute("""
        CREATE TABLE progress_new (
            card_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            due_date DATE NOT NULL,
            interval_days INTEGER NOT NULL DEFAULT 1,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            review_count INTEGER NOT NULL DEFAULT 0,
            last_score INTEGER,
            PRIMARY KEY (card_id, user_id)
        )
    """)
    await db.execute(
        f"INSERT INTO progress_new "
        f"SELECT card_id, {user_id}, due_date, interval_days, ease_factor, review_count, last_score "
        f"FROM progress"
    )
    await db.execute("DROP TABLE progress")
    await db.execute("ALTER TABLE progress_new RENAME TO progress")

async def _migrate_lessons(db) -> None:
    user_id = await _ensure_default_user(db)
    await db.execute("""
        CREATE TABLE lessons_new (
            lesson_id INTEGER NOT NULL,
            unit INTEGER NOT NULL,
            language TEXT NOT NULL DEFAULT 'japanese',
            user_id INTEGER NOT NULL,
            completed_at DATETIME,
            quiz_score TEXT,
            PRIMARY KEY (lesson_id, unit, language, user_id)
        )
    """)
    await db.execute(
        f"INSERT INTO lessons_new "
        f"SELECT lesson_id, unit, 'japanese', {user_id}, completed_at, quiz_score "
        f"FROM lessons"
    )
    await db.execute("DROP TABLE lessons")
    await db.execute("ALTER TABLE lessons_new RENAME TO lessons")

async def init_db():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CARDS)

        # Add language column to cards if upgrading from old schema
        cur = await db.execute("PRAGMA table_info(cards)")
        if "language" not in {r[1] for r in await cur.fetchall()}:
            await db.execute(
                "ALTER TABLE cards ADD COLUMN language TEXT NOT NULL DEFAULT 'japanese'"
            )

        # Migrate or create progress table
        cur = await db.execute("PRAGMA table_info(progress)")
        p_cols = {r[1] for r in await cur.fetchall()}
        if not p_cols:
            await db.execute(CREATE_PROGRESS)
        elif "user_id" not in p_cols:
            await _migrate_progress(db)

        # Migrate or create lessons table
        cur = await db.execute("PRAGMA table_info(lessons)")
        l_cols = {r[1] for r in await cur.fetchall()}
        if not l_cols:
            await db.execute(CREATE_LESSONS)
        elif "user_id" not in l_cols:
            await _migrate_lessons(db)

        await db.commit()

async def get_db():
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        yield db
