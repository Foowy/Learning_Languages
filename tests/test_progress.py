from app.database import get_db
from app.main import app

async def test_due_cards_empty(client):
    response = await client.get("/api/review/due?user_id=1&language=japanese")
    assert response.status_code == 200
    assert response.json() == []

async def test_due_cards_missing_params_rejected(client):
    response = await client.get("/api/review/due")
    assert response.status_code == 422

async def test_update_progress(client):
    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson,language)"
            " VALUES (?,?,?,?,?,?,?)",
            ("hiragana", "あ", "a", "vowel a", 1, 1, "japanese"),
        )
        await db.execute(
            "INSERT INTO progress (card_id, user_id, due_date, interval_days, ease_factor, review_count)"
            " VALUES (1, 1, date('now'), 1, 2.5, 0)"
        )
        await db.commit()
        break
    response = await client.post(
        "/api/review/update?user_id=1",
        json={"card_id": 1, "score": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert "due_date" in data
    assert data["interval_days"] == 1

async def test_update_progress_card_not_in_progress(client):
    response = await client.post(
        "/api/review/update?user_id=1",
        json={"card_id": 999, "score": 3},
    )
    assert response.status_code == 404
