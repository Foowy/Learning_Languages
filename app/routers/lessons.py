from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import aiosqlite
from app.database import get_db
from app.models import LessonComplete

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

@router.get("")
async def list_lessons(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT DISTINCT unit, lesson FROM cards ORDER BY unit, lesson")
    rows = await cursor.fetchall()
    completed_cur = await db.execute(
        "SELECT unit, lesson_id FROM lessons WHERE completed_at IS NOT NULL"
    )
    completed = {(r[0], r[1]) for r in await completed_cur.fetchall()}
    return [{"unit": r[0], "lesson": r[1], "completed": (r[0], r[1]) in completed} for r in rows]

@router.get("/{unit}/{lesson}")
async def get_lesson(unit: int, lesson: int, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT * FROM cards WHERE unit=? AND lesson=? ORDER BY id", (unit, lesson)
    )
    rows = await cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"unit": unit, "lesson": lesson, "cards": [dict(r) for r in rows]}

@router.post("/{unit}/{lesson}/complete")
async def complete_lesson(
    unit: int, lesson: int, body: LessonComplete, db: aiosqlite.Connection = Depends(get_db)
):
    await db.execute(
        "INSERT OR REPLACE INTO lessons (lesson_id, unit, completed_at, quiz_score) VALUES (?,?,?,?)",
        (lesson, unit, datetime.utcnow().isoformat(), body.quiz_score)
    )
    cursor = await db.execute("SELECT id FROM cards WHERE unit=? AND lesson=?", (unit, lesson))
    for row in await cursor.fetchall():
        await db.execute(
            "INSERT OR IGNORE INTO progress (card_id, due_date, interval_days, ease_factor, review_count)"
            " VALUES (?, date('now'), 1, 2.5, 0)",
            (row[0],)
        )
    await db.commit()
    return {"status": "ok"}
