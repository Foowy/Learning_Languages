import io
import json
import logging
import shutil
import tarfile
from pathlib import Path

import aiosqlite
import httpx

import app.database
from app.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(settings.data_dir)
_VERSION_FILE = ".pack-version"


def _stored_version(lessons_dir: Path) -> str:
    vf = lessons_dir / _VERSION_FILE
    return vf.read_text().strip() if vf.exists() else ""


def _needs_download(lessons_dir: Path) -> bool:
    if not lessons_dir.exists() or not any(lessons_dir.rglob("lesson*.json")):
        return True
    target = settings.lessons_pack_version
    return bool(target and _stored_version(lessons_dir) != target)


async def _download_lessons(dest: Path) -> None:
    url = settings.lessons_pack_url
    if not url:
        logger.warning(
            "LESSONS_PACK_URL is not set and no lessons found in %s — "
            "mount a lessons pack or set LESSONS_PACK_URL",
            dest,
        )
        return
    logger.info("Downloading lessons pack from %s", url)
    async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
        resp = await client.get(url)
        resp.raise_for_status()
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(resp.content)) as tar:
        safe = [m for m in tar.getmembers() if not m.name.startswith(("/", ".."))]
        tar.extractall(dest, members=safe)
    if settings.lessons_pack_version:
        (dest / _VERSION_FILE).write_text(settings.lessons_pack_version)
    logger.info("Lessons extracted to %s", dest)


async def seed_if_empty():
    lessons_dir = DATA_DIR / "lessons"
    if _needs_download(lessons_dir):
        await _download_lessons(lessons_dir)

    db_path = app.database.get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return
        lesson_files = sorted(lessons_dir.rglob("lesson*.json")) if lessons_dir.exists() else []
        if not lesson_files:
            return
        for lesson_file in lesson_files:
            # Path structure: lessons_dir/{language}/unit{N}/lesson{N}.json
            rel_parts = lesson_file.relative_to(lessons_dir).parts
            language = rel_parts[0] if len(rel_parts) >= 3 else "japanese"
            data = json.loads(lesson_file.read_text(encoding="utf-8"))
            for card in data["cards"]:
                await db.execute(
                    "INSERT INTO cards (type, character, romaji, meaning, unit, lesson, language, video_path)"
                    " VALUES (?,?,?,?,?,?,?,?)",
                    (
                        card["type"], card["character"], card["romaji"],
                        card["meaning"], data["unit"], data["lesson"], language,
                        card.get("video"),
                    ),
                )
        await db.commit()
