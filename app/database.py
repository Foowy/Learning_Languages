from pathlib import Path
import aiosqlite
from app.config import settings

def get_db_path() -> Path:
    return Path(settings.data_dir) / "progress.db"

CREATE_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    character TEXT NOT NULL,
    romaji TEXT NOT NULL,
    meaning TEXT NOT NULL,
    unit INTEGER NOT NULL,
    lesson INTEGER NOT NULL,
    audio_path TEXT
)
"""

CREATE_PROGRESS = """
CREATE TABLE IF NOT EXISTS progress (
    card_id INTEGER PRIMARY KEY REFERENCES cards(id),
    due_date DATE NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_score INTEGER
)
"""

CREATE_LESSONS = """
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER NOT NULL,
    unit INTEGER NOT NULL,
    completed_at DATETIME,
    quiz_score TEXT,
    PRIMARY KEY (lesson_id, unit)
)
"""

async def init_db():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()

async def get_db():
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        yield db
