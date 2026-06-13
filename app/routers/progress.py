from fastapi import APIRouter, Depends
import aiosqlite
from app.database import get_db
from app.models import ReviewUpdate
from app.services.srs import SRSCard, next_interval, due_date

router = APIRouter(prefix="/api/review", tags=["review"])

@router.get("/due")
async def get_due_cards(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("""
        SELECT c.*, p.due_date, p.interval_days, p.ease_factor, p.review_count, p.last_score
        FROM progress p JOIN cards c ON c.id = p.card_id
        WHERE p.due_date <= date('now') ORDER BY p.due_date
    """)
    return [dict(r) for r in await cursor.fetchall()]

@router.post("/update")
async def update_progress(update: ReviewUpdate, db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute(
        "SELECT interval_days, ease_factor, review_count FROM progress WHERE card_id=?",
        (update.card_id,)
    )
    row = await cursor.fetchone()
    if not row:
        return {"error": "card not in progress"}
    card = SRSCard(interval_days=row[0], ease_factor=row[1], review_count=row[2])
    updated = next_interval(card, update.score)
    new_due = due_date(updated.interval_days)
    await db.execute(
        "UPDATE progress SET due_date=?, interval_days=?, ease_factor=?, review_count=?, last_score=?"
        " WHERE card_id=?",
        (new_due.isoformat(), updated.interval_days, updated.ease_factor,
         updated.review_count, update.score, update.card_id)
    )
    await db.commit()
    return {"due_date": new_due.isoformat(), "interval_days": updated.interval_days}
