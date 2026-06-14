from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime
import aiosqlite
from app.database import get_db
from app.models import LessonComplete

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

@router.get("")
async def list_lessons(
    user_id: int = Query(...),
    language: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT DISTINCT unit, lesson FROM cards WHERE language=? ORDER BY unit, lesson",
        (language,),
    )
    rows = await cursor.fetchall()
    completed_cur = await db.execute(
        "SELECT unit, lesson_id FROM lessons"
        " WHERE user_id=? AND language=? AND completed_at IS NOT NULL",
        (user_id, language),
    )
    completed = {(r[0], r[1]) for r in await completed_cur.fetchall()}
    return [{"unit": r[0], "lesson": r[1], "completed": (r[0], r[1]) in completed} for r in rows]

@router.get("/{unit}/{lesson}")
async def get_lesson(
    unit: int,
    lesson: int,
    language: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT * FROM cards WHERE unit=? AND lesson=? AND language=? ORDER BY id",
        (unit, lesson, language),
    )
    rows = await cursor.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return {"unit": unit, "lesson": lesson, "cards": [dict(r) for r in rows]}

@router.post("/{unit}/{lesson}/complete")
async def complete_lesson(
    unit: int,
    lesson: int,
    body: LessonComplete,
    user_id: int = Query(...),
    language: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    await db.execute(
        "INSERT OR REPLACE INTO lessons (lesson_id, unit, language, user_id, completed_at, quiz_score)"
        " VALUES (?,?,?,?,?,?)",
        (lesson, unit, language, user_id, datetime.utcnow().isoformat(), body.quiz_score),
    )
    cursor = await db.execute(
        "SELECT id FROM cards WHERE unit=? AND lesson=? AND language=?",
        (unit, lesson, language),
    )
    for row in await cursor.fetchall():
        await db.execute(
            "INSERT OR IGNORE INTO progress"
            " (card_id, user_id, due_date, interval_days, ease_factor, review_count)"
            " VALUES (?, ?, date('now'), 1, 2.5, 0)",
            (row[0], user_id),
        )
    await db.commit()
    return {"status": "ok"}
