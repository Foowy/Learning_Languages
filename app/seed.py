import json
import shutil
from pathlib import Path
import aiosqlite
from app.config import settings
import app.database

DATA_DIR = Path(settings.data_dir)
BUNDLED_LESSONS = Path(__file__).parent.parent / "lessons"

async def seed_if_empty():
    lessons_dir = DATA_DIR / "lessons"
    if not lessons_dir.exists() or not any(lessons_dir.rglob("lesson*.json")):
        shutil.copytree(BUNDLED_LESSONS, lessons_dir, dirs_exist_ok=True)

    db_path = app.database.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return
        for lesson_file in sorted(lessons_dir.rglob("lesson*.json")):
            # Path structure: lessons_dir/{language}/unit{N}/lesson{N}.json
            rel_parts = lesson_file.relative_to(lessons_dir).parts
            language = rel_parts[0] if len(rel_parts) >= 3 else "japanese"
            data = json.loads(lesson_file.read_text(encoding="utf-8"))
            for card in data["cards"]:
                await db.execute(
                    "INSERT INTO cards (type, character, romaji, meaning, unit, lesson, language)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (
                        card["type"], card["character"], card["romaji"],
                        card["meaning"], data["unit"], data["lesson"], language,
                    ),
                )
        await db.commit()
