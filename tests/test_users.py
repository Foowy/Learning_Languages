import io
from PIL import Image
from app.main import app
from app.database import get_db

async def test_list_users_returns_seeded_tester(client):
    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tester"
    assert data[0]["id"] == 1
    assert data[0]["avatar_url"] is None

async def test_create_user(client):
    response = await client.post("/api/users", json={"name": "Alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert data["id"] == 2
    assert data["avatar_url"] is None

async def test_create_user_empty_name_rejected(client):
    response = await client.post("/api/users", json={"name": "  "})
    assert response.status_code == 422

async def test_upload_avatar(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.users.settings.data_dir", str(tmp_path))
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    response = await client.post(
        "/api/users/1/avatar",
        files={"avatar": ("photo.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["avatar_url"] == "/avatars/1.jpg"
    assert (tmp_path / "avatars" / "1.jpg").exists()

async def test_upload_avatar_user_not_found(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.users.settings.data_dir", str(tmp_path))
    img = Image.new("RGB", (10, 10))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    response = await client.post(
        "/api/users/999/avatar",
        files={"avatar": ("x.jpg", buf, "image/jpeg")}
    )
    assert response.status_code == 404
