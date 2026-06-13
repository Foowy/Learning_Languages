import io
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import aiosqlite
from app.database import get_db
from app.models import UserCreate
from app.config import settings

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("")
async def list_users(db: aiosqlite.Connection = Depends(get_db)):
    cursor = await db.execute("SELECT id, name, avatar_path FROM users ORDER BY id")
    rows = await cursor.fetchall()
    return [
        {
            "id": r[0],
            "name": r[1],
            "avatar_url": f"/avatars/{r[0]}.jpg" if r[2] else None,
        }
        for r in rows
    ]

@router.post("")
async def create_user(body: UserCreate, db: aiosqlite.Connection = Depends(get_db)):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name required")
    cursor = await db.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = cursor.lastrowid
    await db.commit()
    return {"id": user_id, "name": name, "avatar_url": None}

@router.post("/{user_id}/avatar")
async def upload_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    from PIL import Image

    cursor = await db.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="user not found")

    data = await avatar.read()
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((512, 512))

    avatars_dir = Path(settings.data_dir) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)
    out_path = avatars_dir / f"{user_id}.jpg"
    img.save(str(out_path), "JPEG", quality=85)

    await db.execute("UPDATE users SET avatar_path=? WHERE id=?", (str(out_path), user_id))
    await db.commit()
    return {"avatar_url": f"/avatars/{user_id}.jpg"}
