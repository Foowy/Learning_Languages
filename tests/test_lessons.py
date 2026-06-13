from app.database import get_db
from app.main import app

async def test_list_lessons_empty(client):
    response = await client.get("/api/lessons")
    assert response.status_code == 200
    assert response.json() == []

async def test_get_lesson_not_found(client):
    response = await client.get("/api/lessons/1/1")
    assert response.status_code == 404

async def test_complete_lesson_adds_to_progress(client):
    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson) VALUES (?,?,?,?,?,?)",
            ("hiragana","あ","a","vowel a",1,1)
        )
        await db.commit()
        break
    response = await client.post("/api/lessons/1/1/complete", json={"quiz_score": "5/5"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
