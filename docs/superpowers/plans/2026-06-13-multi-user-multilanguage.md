# Multi-User & Multi-Language Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add family user profiles (no auth, pick-a-profile UI) and multi-language support (Japanese, Latin American Spanish, ASL via video) with per-user per-language progress tracked in a shared SQLite DB.

**Architecture:** Single `progress.db` gains a `users` table plus `user_id`/`language` columns on `progress` and `lessons`; startup migration preserves existing data. Language folders under `/data/lessons/` are auto-discovered. Session state (`userId`, `currentLanguage`) stored in `sessionStorage`; all API calls append these as query params via a shared `window.apiParams()` helper. Two new frontend screens (user picker, language picker) gate entry to the app. ASL lessons skip TTS/STT phases and render `<video>` in introduce.

**Tech Stack:** Same stack as existing (Python 3.11, FastAPI 0.111.0, aiosqlite, pydantic-settings, pytest + pytest-asyncio asyncio_mode=auto, vanilla HTML/CSS/JS). New addition: `Pillow` for avatar JPEG resizing.

---

## File Structure

```
Learning_Languages/
├── app/
│   ├── database.py          MODIFY — new CREATE_USERS DDL, updated CREATE_PROGRESS/LESSONS PKs, migration in init_db()
│   ├── models.py            MODIFY — add UserCreate model
│   ├── seed.py              MODIFY — scan lessons/{language}/ dirs, insert language column
│   ├── main.py              MODIFY — register new routers, /avatars + /videos static mounts
│   └── routers/
│       ├── lessons.py       MODIFY — add user_id + language query params throughout
│       ├── progress.py      MODIFY — add user_id + language query params
│       ├── users.py         CREATE — GET/POST /api/users, POST /api/users/{id}/avatar
│       └── languages.py     CREATE — GET /api/languages (scan lessons/ dir)
├── frontend/
│   ├── index.html           MODIFY — title, nav language/user buttons, new script tags
│   └── js/
│       ├── app.js           MODIFY — sessionStorage helpers, startup gating, switchUser
│       ├── users.js         CREATE — profile picker + create form
│       ├── languages.js     CREATE — language picker screen
│       ├── dashboard.js     MODIFY — apiParams() on all fetches
│       ├── lesson.js        MODIFY — apiParams() on all fetches, ASL video/phase handling
│       ├── review.js        MODIFY — apiParams() on all fetches
│       └── speak.js         MODIFY — apiParams() on all fetches
├── lessons/
│   └── japanese/            RENAME from unit1/ → japanese/unit1/, unit2/ → japanese/unit2/
│       ├── unit1/           (existing 20 hiragana lessons, relocated)
│       └── unit2/           (existing 20 katakana lessons, relocated)
├── tests/
│   ├── conftest.py          MODIFY — import CREATE_USERS, create test user in fixtures
│   ├── test_database.py     MODIFY — assert 'users' in tables
│   ├── test_seed.py         MODIFY — use japanese/unit1/ path, add language column check
│   ├── test_lessons.py      MODIFY — add user_id + language params, language column in inserts
│   ├── test_progress.py     MODIFY — add user_id param, user_id in inserts
│   ├── test_users.py        CREATE — list + create user tests
│   └── test_languages.py   CREATE — list languages tests
├── requirements.txt         MODIFY — add Pillow==10.3.0
└── Dockerfile               MODIFY — add libjpeg-dev to apt install
```

---

## Task 1: Reorganize Lesson Files

**Files:**
- `lessons/unit1/` → `lessons/japanese/unit1/`
- `lessons/unit2/` → `lessons/japanese/unit2/`

**Context:** The current lesson JSONs live at `lessons/unit1/lesson01.json`. The new multi-language layout requires a language subfolder: `lessons/japanese/unit1/lesson01.json`. This is a pure file move — no JSON content changes. Use `git mv` to preserve history.

- [ ] **Step 1: Create the japanese subfolder and move files**

```bash
mkdir -p lessons/japanese
git mv lessons/unit1 lessons/japanese/unit1
git mv lessons/unit2 lessons/japanese/unit2
```

- [ ] **Step 2: Verify the move**

```bash
ls lessons/japanese/unit1/ | head -5
ls lessons/japanese/unit2/ | head -5
```

Expected: `lesson01.json lesson02.json ...` in both dirs.

- [ ] **Step 3: Verify existing tests still pass (seed test will fail — that's expected until Task 6)**

```bash
pytest tests/test_database.py tests/test_srs.py -v
```

Expected: all pass. `test_seed.py` will fail after this — that is expected and will be fixed in Task 6.

- [ ] **Step 4: Commit**

```bash
git add lessons/
git commit -m "refactor: move lessons into lessons/japanese/ subfolder for multi-language support"
git push
```

---

## Task 2: Database Schema + Migration

**Files:**
- Modify: `app/database.py`
- Modify: `tests/conftest.py`
- Modify: `tests/test_database.py`

**Context:** The current DB has `cards`, `progress`, `lessons` tables with no user concept. We're adding a `users` table, a `language` column to `cards`, and `user_id` + `language` to the primary keys of `progress` and `lessons`. `init_db()` must detect old schema and migrate in-place, assigning existing rows to a default "Player 1" user. The `conftest.py` fixtures import the DDL strings — they must be updated to include `CREATE_USERS`.

- [ ] **Step 1: Write failing tests**

Replace `tests/test_database.py` entirely:

```python
import pytest
import aiosqlite

@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.get_db_path", lambda: tmp_path / "test.db")
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in await cursor.fetchall()}
    assert {"users", "cards", "progress", "lessons"} <= tables

@pytest.mark.asyncio
async def test_init_db_migration_adds_user_id_to_progress(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.get_db_path", lambda: tmp_path / "test.db")
    # Create old-schema progress table (no user_id)
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        await db.execute("""CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, avatar_path TEXT, created_at DATETIME NOT NULL DEFAULT (datetime('now')))""")
        await db.execute("""CREATE TABLE cards (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, character TEXT NOT NULL, romaji TEXT NOT NULL, meaning TEXT NOT NULL, unit INTEGER NOT NULL, lesson INTEGER NOT NULL, language TEXT NOT NULL DEFAULT 'japanese', audio_path TEXT)""")
        await db.execute("""CREATE TABLE progress (card_id INTEGER PRIMARY KEY, due_date DATE NOT NULL, interval_days INTEGER NOT NULL DEFAULT 1, ease_factor REAL NOT NULL DEFAULT 2.5, review_count INTEGER NOT NULL DEFAULT 0, last_score INTEGER)""")
        await db.execute("""CREATE TABLE lessons (lesson_id INTEGER NOT NULL, unit INTEGER NOT NULL, completed_at DATETIME, quiz_score TEXT, PRIMARY KEY (lesson_id, unit))""")
        await db.execute("INSERT INTO cards (type,character,romaji,meaning,unit,lesson) VALUES ('hiragana','あ','a','vowel',1,1)")
        await db.execute("INSERT INTO progress (card_id, due_date, interval_days, ease_factor, review_count) VALUES (1, date('now'), 1, 2.5, 0)")
        await db.execute("INSERT INTO lessons (lesson_id, unit, completed_at) VALUES (1, 1, datetime('now'))")
        await db.commit()
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        cursor = await db.execute("PRAGMA table_info(progress)")
        cols = {r[1] for r in await cursor.fetchall()}
        assert "user_id" in cols
        cursor = await db.execute("PRAGMA table_info(lessons)")
        cols = {r[1] for r in await cursor.fetchall()}
        assert "user_id" in cols
        assert "language" in cols
        # Default user was created
        cursor = await db.execute("SELECT name FROM users")
        users = [r[0] for r in await cursor.fetchall()]
        assert "Player 1" in users
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_database.py -v
```

Expected: FAIL (users table missing, no user_id column).

- [ ] **Step 3: Rewrite `app/database.py`**

```python
from pathlib import Path
import aiosqlite
from app.config import settings

def get_db_path() -> Path:
    return Path(settings.data_dir) / "progress.db"

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    avatar_path TEXT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
)
"""

CREATE_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    character TEXT NOT NULL,
    romaji TEXT NOT NULL,
    meaning TEXT NOT NULL,
    unit INTEGER NOT NULL,
    lesson INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT 'japanese',
    audio_path TEXT
)
"""

CREATE_PROGRESS = """
CREATE TABLE IF NOT EXISTS progress (
    card_id INTEGER NOT NULL REFERENCES cards(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    due_date DATE NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_score INTEGER,
    PRIMARY KEY (card_id, user_id)
)
"""

CREATE_LESSONS = """
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER NOT NULL,
    unit INTEGER NOT NULL,
    language TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    completed_at DATETIME,
    quiz_score TEXT,
    PRIMARY KEY (lesson_id, unit, language, user_id)
)
"""

async def _ensure_default_user(db) -> int:
    cursor = await db.execute("SELECT COUNT(*) FROM users")
    if (await cursor.fetchone())[0] == 0:
        await db.execute("INSERT INTO users (name) VALUES ('Player 1')")
    cursor = await db.execute("SELECT id FROM users ORDER BY id LIMIT 1")
    return (await cursor.fetchone())[0]

async def _migrate_progress(db) -> None:
    user_id = await _ensure_default_user(db)
    await db.execute("""
        CREATE TABLE progress_new (
            card_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            due_date DATE NOT NULL,
            interval_days INTEGER NOT NULL DEFAULT 1,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            review_count INTEGER NOT NULL DEFAULT 0,
            last_score INTEGER,
            PRIMARY KEY (card_id, user_id)
        )
    """)
    await db.execute(
        f"INSERT INTO progress_new "
        f"SELECT card_id, {user_id}, due_date, interval_days, ease_factor, review_count, last_score "
        f"FROM progress"
    )
    await db.execute("DROP TABLE progress")
    await db.execute("ALTER TABLE progress_new RENAME TO progress")

async def _migrate_lessons(db) -> None:
    user_id = await _ensure_default_user(db)
    await db.execute("""
        CREATE TABLE lessons_new (
            lesson_id INTEGER NOT NULL,
            unit INTEGER NOT NULL,
            language TEXT NOT NULL DEFAULT 'japanese',
            user_id INTEGER NOT NULL,
            completed_at DATETIME,
            quiz_score TEXT,
            PRIMARY KEY (lesson_id, unit, language, user_id)
        )
    """)
    await db.execute(
        f"INSERT INTO lessons_new "
        f"SELECT lesson_id, unit, 'japanese', {user_id}, completed_at, quiz_score "
        f"FROM lessons"
    )
    await db.execute("DROP TABLE lessons")
    await db.execute("ALTER TABLE lessons_new RENAME TO lessons")

async def init_db():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CARDS)

        # Add language column to cards if upgrading from old schema
        cur = await db.execute("PRAGMA table_info(cards)")
        if "language" not in {r[1] for r in await cur.fetchall()}:
            await db.execute(
                "ALTER TABLE cards ADD COLUMN language TEXT NOT NULL DEFAULT 'japanese'"
            )

        # Migrate or create progress table
        cur = await db.execute("PRAGMA table_info(progress)")
        p_cols = {r[1] for r in await cur.fetchall()}
        if not p_cols:
            await db.execute(CREATE_PROGRESS)
        elif "user_id" not in p_cols:
            await _migrate_progress(db)

        # Migrate or create lessons table
        cur = await db.execute("PRAGMA table_info(lessons)")
        l_cols = {r[1] for r in await cur.fetchall()}
        if not l_cols:
            await db.execute(CREATE_LESSONS)
        elif "user_id" not in l_cols:
            await _migrate_lessons(db)

        await db.commit()

async def get_db():
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        yield db
```

- [ ] **Step 4: Update `tests/conftest.py`**

```python
import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

from app.database import CREATE_USERS, CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS, get_db

@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.execute("INSERT INTO users (name) VALUES ('Tester')")
        await db.commit()
        yield db

@pytest_asyncio.fixture
async def client(tmp_path):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as setup_db:
        await setup_db.execute(CREATE_USERS)
        await setup_db.execute(CREATE_CARDS)
        await setup_db.execute(CREATE_PROGRESS)
        await setup_db.execute(CREATE_LESSONS)
        await setup_db.execute("INSERT INTO users (name) VALUES ('Tester')")
        await setup_db.commit()

    async def override_get_db():
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    from app.main import app
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_database.py -v
```

Expected: both tests PASS.

- [ ] **Step 6: Commit**

```bash
git add app/database.py tests/conftest.py tests/test_database.py
git commit -m "feat: multi-user DB schema with migration (users table, user_id + language on progress/lessons)"
git push
```

---

## Task 3: Pillow Dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `Dockerfile`

**Context:** Avatar upload uses Pillow for JPEG resizing. Pillow's PyPI wheel bundles libjpeg for most platforms, but `python:3.11-slim` (Debian Bullseye) may not include libjpeg. Adding `libjpeg-dev` to the Dockerfile `apt install` line is the safe approach.

- [ ] **Step 1: Update `requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
aiosqlite==0.20.0
pydantic-settings==2.2.1
edge-tts==6.1.9
openai-whisper==20231117
python-multipart==0.0.9
httpx==0.27.0
Pillow==10.3.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 2: Update `Dockerfile`**

Change the `apt-get install` line to add `libjpeg-dev`:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg libjpeg-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Whisper base model during build (avoids slow first-start)
RUN python -c "import whisper; whisper.load_model('base')"

COPY app/ app/
COPY frontend/ frontend/
COPY lessons/ lessons/

ENV DATA_DIR=/data
ENV CONFIG_DIR=/config
ENV PORT=13200

EXPOSE 13200

CMD ["python", "-m", "app.main"]
```

- [ ] **Step 3: Install locally and verify import**

```bash
pip install Pillow==10.3.0
python -c "from PIL import Image; print('Pillow OK')"
```

Expected: `Pillow OK`

- [ ] **Step 4: Run existing tests to confirm nothing broken**

```bash
pytest tests/ -v --ignore=tests/test_seed.py
```

Expected: all pass (test_seed.py is excluded; it's broken until Task 6).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt Dockerfile
git commit -m "chore: add Pillow for avatar image processing"
git push
```

---

## Task 4: Users API

**Files:**
- Create: `app/routers/users.py`
- Modify: `app/models.py`
- Modify: `app/main.py`
- Create: `tests/test_users.py`

**Context:** Three endpoints: list profiles, create profile, upload avatar. Avatar is stored as JPEG at `/data/avatars/{user_id}.jpg` and served via a `/avatars` static mount. `app/main.py` registers the new router and mounts `/avatars` and `/videos` directories (created lazily in startup). The conftest `client` fixture creates a "Tester" user with `id=1` — tests rely on that.

- [ ] **Step 1: Write failing tests**

Create `tests/test_users.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_users.py -v
```

Expected: FAIL (404 on /api/users).

- [ ] **Step 3: Add `UserCreate` model to `app/models.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class UserCreate(BaseModel):
    name: str

class ReviewUpdate(BaseModel):
    card_id: int
    score: int = Field(ge=1, le=4)

class LessonComplete(BaseModel):
    quiz_score: str

class TranscriptionResult(BaseModel):
    text: str
    expected: str
    match: bool
```

- [ ] **Step 4: Create `app/routers/users.py`**

```python
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
```

- [ ] **Step 5: Update `app/main.py`**

```python
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.seed import seed_if_empty
from app.routers.lessons import router as lessons_router
from app.routers.progress import router as progress_router
from app.routers.speech import router as speech_router
from app.routers.users import router as users_router
from app.routers.languages import router as languages_router

app = FastAPI(title="Learning Languages")

app.include_router(users_router)
app.include_router(languages_router)
app.include_router(lessons_router)
app.include_router(progress_router)
app.include_router(speech_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.mount("/avatars", StaticFiles(directory=str(Path(settings.data_dir) / "avatars"), check_dir=False), name="avatars")
app.mount("/videos", StaticFiles(directory=str(Path(settings.data_dir) / "videos"), check_dir=False), name="videos")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.on_event("startup")
async def startup():
    (Path(settings.data_dir) / "avatars").mkdir(parents=True, exist_ok=True)
    (Path(settings.data_dir) / "videos").mkdir(parents=True, exist_ok=True)
    await init_db()
    await seed_if_empty()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=False)
```

Note: `languages_router` is imported here but created in Task 5. Create a stub `app/routers/languages.py` now so the import doesn't fail:

```python
# app/routers/languages.py (stub — full implementation in Task 5)
from fastapi import APIRouter
router = APIRouter(prefix="/api/languages", tags=["languages"])

@router.get("")
async def list_languages():
    return []
```

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_users.py -v
```

Expected: all 5 PASS.

- [ ] **Step 7: Run full suite (excluding test_seed.py)**

```bash
pytest tests/ -v --ignore=tests/test_seed.py
```

Expected: all pass.

- [ ] **Step 8: Commit**

```bash
git add app/routers/users.py app/routers/languages.py app/models.py app/main.py tests/test_users.py
git commit -m "feat: users API (list, create, avatar upload) and app wiring"
git push
```

---

## Task 5: Languages API

**Files:**
- Modify: `app/routers/languages.py` (replace stub from Task 4)
- Create: `tests/test_languages.py`

**Context:** `GET /api/languages` scans `/data/lessons/` for subdirectories, counts `lesson*.json` files in each, and returns a list with language key, display label, and count. The label mapping is hardcoded in the router. Tests monkeypatch `settings.data_dir` to a tmp dir so they don't depend on `/data`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_languages.py`:

```python
import pytest
from unittest.mock import MagicMock

def _mock_settings(tmp_path):
    m = MagicMock()
    m.data_dir = str(tmp_path)
    return m

async def test_list_languages_no_lessons_dir(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    response = await client.get("/api/languages")
    assert response.status_code == 200
    assert response.json() == []

async def test_list_languages_japanese(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    jp = tmp_path / "lessons" / "japanese" / "unit1"
    jp.mkdir(parents=True)
    (jp / "lesson01.json").write_text("{}")
    (jp / "lesson02.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["language"] == "japanese"
    assert data[0]["label"] == "🇯🇵 Japanese"
    assert data[0]["lesson_count"] == 2

async def test_list_languages_multiple(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    for lang in ["japanese", "spanish"]:
        d = tmp_path / "lessons" / lang / "unit1"
        d.mkdir(parents=True)
        (d / "lesson01.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    langs = {d["language"] for d in data}
    assert langs == {"japanese", "spanish"}

async def test_list_languages_unknown_folder_capitalized(client, tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.languages.settings", _mock_settings(tmp_path))
    d = tmp_path / "lessons" / "klingon" / "unit1"
    d.mkdir(parents=True)
    (d / "lesson01.json").write_text("{}")
    response = await client.get("/api/languages")
    assert response.status_code == 200
    assert response.json()[0]["label"] == "Klingon"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_languages.py -v
```

Expected: FAIL (stub returns [] for everything — `test_list_languages_japanese` fails).

- [ ] **Step 3: Replace stub with full implementation of `app/routers/languages.py`**

```python
from pathlib import Path
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/languages", tags=["languages"])

LANGUAGE_LABELS = {
    "japanese": "🇯🇵 Japanese",
    "spanish": "🇪🇸 Spanish (Latin America)",
    "asl": "🤟 ASL",
}

@router.get("")
async def list_languages():
    lessons_dir = Path(settings.data_dir) / "lessons"
    if not lessons_dir.exists():
        return []
    result = []
    for lang_dir in sorted(lessons_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        lesson_count = sum(1 for _ in lang_dir.rglob("lesson*.json"))
        label = LANGUAGE_LABELS.get(lang_dir.name, lang_dir.name.capitalize())
        result.append({
            "language": lang_dir.name,
            "label": label,
            "lesson_count": lesson_count,
        })
    return result
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_languages.py -v
```

Expected: all 4 PASS.

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -v --ignore=tests/test_seed.py
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/routers/languages.py tests/test_languages.py
git commit -m "feat: languages API (auto-discover language folders)"
git push
```

---

## Task 6: Seed Update

**Files:**
- Modify: `app/seed.py`
- Modify: `tests/test_seed.py`

**Context:** After Task 1, lessons live at `lessons/japanese/unit1/lesson01.json`. The seed must extract the language name from the path (it's the first subfolder under `lessons/`) and insert it into the `language` column of `cards`. The test fixture must also use the new path layout.

- [ ] **Step 1: Update `tests/test_seed.py`**

```python
import json
import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
from app.database import CREATE_USERS, CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS
from app.seed import seed_if_empty

@pytest_asyncio.fixture
async def seeded_db(tmp_path):
    lesson_dir = tmp_path / "lessons" / "japanese" / "unit1"
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "lesson01.json").write_text(json.dumps({
        "unit": 1, "lesson": 1, "title": "Test",
        "cards": [
            {"type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel a"}
        ]
    }), encoding="utf-8")
    db_path = tmp_path / "progress.db"
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()
    return tmp_path

async def test_seed_inserts_cards_with_language(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.seed.app.database.get_db_path", lambda: seeded_db / "progress.db")
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT language FROM cards LIMIT 1")
        language = (await cursor.fetchone())[0]
    assert count == 1
    assert language == "japanese"

async def test_seed_is_idempotent(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.seed.app.database.get_db_path", lambda: seeded_db / "progress.db")
    await seed_if_empty()
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
    assert count == 1
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_seed.py -v
```

Expected: FAIL (`test_seed_inserts_cards_with_language` fails — no language column inserted).

- [ ] **Step 3: Rewrite `app/seed.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_seed.py -v
```

Expected: both PASS.

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/seed.py tests/test_seed.py
git commit -m "feat: seed reads language from folder path, inserts language column"
git push
```

---

## Task 7: Lessons Router Update

**Files:**
- Modify: `app/routers/lessons.py`
- Modify: `tests/test_lessons.py`

**Context:** All three lesson endpoints now require `user_id` (int, query param) and `language` (str, query param). The `list_lessons` endpoint filters cards by language and looks up completed lessons for the specific user+language pair. `complete_lesson` uses the new `(lesson_id, unit, language, user_id)` PK, and adds cards to `progress` with `user_id`. Tests must pass these params and insert cards with the `language` column.

- [ ] **Step 1: Write updated tests**

Replace `tests/test_lessons.py` entirely:

```python
from app.database import get_db
from app.main import app

async def test_list_lessons_empty(client):
    response = await client.get("/api/lessons?user_id=1&language=japanese")
    assert response.status_code == 200
    assert response.json() == []

async def test_get_lesson_not_found(client):
    response = await client.get("/api/lessons/1/1?language=japanese")
    assert response.status_code == 404

async def test_list_lessons_missing_params_rejected(client):
    response = await client.get("/api/lessons")
    assert response.status_code == 422

async def test_complete_lesson_adds_to_progress(client):
    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson,language)"
            " VALUES (?,?,?,?,?,?,?)",
            ("hiragana", "あ", "a", "vowel a", 1, 1, "japanese"),
        )
        await db.commit()
        break
    response = await client.post(
        "/api/lessons/1/1/complete?user_id=1&language=japanese",
        json={"quiz_score": "5/5"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

async def test_list_lessons_shows_completed(client):
    async for db in app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson,language)"
            " VALUES (?,?,?,?,?,?,?)",
            ("hiragana", "あ", "a", "vowel a", 1, 1, "japanese"),
        )
        await db.commit()
        break
    await client.post(
        "/api/lessons/1/1/complete?user_id=1&language=japanese",
        json={"quiz_score": "5/5"},
    )
    response = await client.get("/api/lessons?user_id=1&language=japanese")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["completed"] is True
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_lessons.py -v
```

Expected: FAIL (endpoints don't accept user_id/language yet).

- [ ] **Step 3: Rewrite `app/routers/lessons.py`**

```python
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
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_lessons.py -v
```

Expected: all 5 PASS.

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/routers/lessons.py tests/test_lessons.py
git commit -m "feat: lessons router requires user_id + language query params"
git push
```

---

## Task 8: Progress Router Update

**Files:**
- Modify: `app/routers/progress.py`
- Modify: `tests/test_progress.py`

**Context:** `GET /api/review/due` needs `user_id` and `language` to filter by user and language. `POST /api/review/update` needs `user_id` as a query param so it can look up and update the `(card_id, user_id)` row. Tests insert cards with the `language` column and progress with `user_id`.

- [ ] **Step 1: Write updated tests**

Replace `tests/test_progress.py` entirely:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_progress.py -v
```

Expected: FAIL.

- [ ] **Step 3: Rewrite `app/routers/progress.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
import aiosqlite
from app.database import get_db
from app.models import ReviewUpdate
from app.services.srs import SRSCard, next_interval, due_date

router = APIRouter(prefix="/api/review", tags=["review"])

@router.get("/due")
async def get_due_cards(
    user_id: int = Query(...),
    language: str = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        """
        SELECT c.*, p.due_date, p.interval_days, p.ease_factor, p.review_count, p.last_score
        FROM progress p JOIN cards c ON c.id = p.card_id
        WHERE p.due_date <= date('now') AND p.user_id=? AND c.language=?
        ORDER BY p.due_date
        """,
        (user_id, language),
    )
    return [dict(r) for r in await cursor.fetchall()]

@router.post("/update")
async def update_progress(
    update: ReviewUpdate,
    user_id: int = Query(...),
    db: aiosqlite.Connection = Depends(get_db),
):
    cursor = await db.execute(
        "SELECT interval_days, ease_factor, review_count FROM progress"
        " WHERE card_id=? AND user_id=?",
        (update.card_id, user_id),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="card not in progress")
    card = SRSCard(interval_days=row[0], ease_factor=row[1], review_count=row[2])
    updated = next_interval(card, update.score)
    new_due = due_date(updated.interval_days)
    await db.execute(
        "UPDATE progress SET due_date=?, interval_days=?, ease_factor=?, review_count=?, last_score=?"
        " WHERE card_id=? AND user_id=?",
        (
            new_due.isoformat(), updated.interval_days, updated.ease_factor,
            updated.review_count, update.score, update.card_id, user_id,
        ),
    )
    await db.commit()
    return {"due_date": new_due.isoformat(), "interval_days": updated.interval_days}
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_progress.py -v
```

Expected: all 4 PASS.

- [ ] **Step 5: Run full suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add app/routers/progress.py tests/test_progress.py
git commit -m "feat: progress router requires user_id + language query params"
git push
```

---

## Task 9: Frontend index.html + Nav

**Files:**
- Modify: `frontend/index.html`

**Context:** The HTML shell needs: (1) updated title and logo, (2) a language switcher button and a user switcher button in the top nav, (3) `<script>` tags for the two new JS files. The language button calls `renderLanguagePicker()` (defined in `languages.js`). The user button calls `window.switchUser()` (defined in `app.js`). Both functions will be available by the time the user can click them (all scripts loaded). Load order: audio.js → users.js → languages.js → dashboard.js → lesson.js → review.js → speak.js → app.js.

- [ ] **Step 1: Replace `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Learning Languages</title>
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <nav class="top-nav">
    <span class="logo">学ぶ</span>
    <div class="nav-links">
      <a href="#home" class="nav-link" data-page="home">Home</a>
      <a href="#lessons" class="nav-link" data-page="lessons">Lessons</a>
      <a href="#review" class="nav-link" data-page="review">Review</a>
      <a href="#speak" class="nav-link" data-page="speak">Speak</a>
    </div>
    <button id="lang-btn" class="btn btn-secondary" style="padding:4px 10px;font-size:13px" onclick="renderLanguagePicker()">🌐</button>
    <button id="user-btn" class="btn btn-secondary" style="padding:4px 10px;font-size:13px" onclick="window.switchUser()">👤</button>
    <button class="hamburger" id="hamburger">☰</button>
  </nav>
  <div class="mobile-menu" id="mobile-menu">
    <a href="#home" class="nav-link" data-page="home">Home</a>
    <a href="#lessons" class="nav-link" data-page="lessons">Lessons</a>
    <a href="#review" class="nav-link" data-page="review">Review</a>
    <a href="#speak" class="nav-link" data-page="speak">Speak</a>
    <button class="btn btn-secondary" style="margin:8px 0" onclick="renderLanguagePicker()">🌐 Switch Language</button>
    <button class="btn btn-secondary" onclick="window.switchUser()">👤 Switch User</button>
  </div>
  <main id="app"></main>
  <script src="/static/js/audio.js"></script>
  <script src="/static/js/users.js"></script>
  <script src="/static/js/languages.js"></script>
  <script src="/static/js/dashboard.js"></script>
  <script src="/static/js/lesson.js"></script>
  <script src="/static/js/review.js"></script>
  <script src="/static/js/speak.js"></script>
  <script src="/static/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Run full test suite (backend only — frontend is verified by eye)**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/index.html
git commit -m "feat: update index.html with language/user nav buttons and new script tags"
git push
```

---

## Task 10: Frontend users.js

**Files:**
- Create: `frontend/js/users.js`

**Context:** This file owns the profile picker screen. It's loaded before `app.js` so `renderUserPicker` is defined when `app.js` calls it. It hides the nav during selection, shows user cards with avatar or CSS initials fallback, renders a "+ New Profile" card that expands a form (name + optional avatar upload). On successful selection, sets `sessionStorage.userId` and `sessionStorage.userName`, shows nav, then checks for language selection.

- [ ] **Step 1: Create `frontend/js/users.js`**

```javascript
async function renderUserPicker() {
  document.querySelector('.top-nav').style.display = 'none';
  const app = document.getElementById('app');
  const users = await fetch('/api/users').then(r => r.json());

  app.innerHTML = `
    <div style="text-align:center;padding:40px 0 20px">
      <h2>Who\\'s learning today?</h2>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:16px;justify-content:center;margin-bottom:24px">
      ${users.map(u => `
        <div class="card" style="text-align:center;padding:20px;cursor:pointer;min-width:100px"
             onclick="window.selectUser(${u.id},'${u.name.replace(/'/g, "\\\\'")}')">
          ${u.avatar_url
            ? `<img src="${u.avatar_url}" style="width:64px;height:64px;border-radius:50%;object-fit:cover;margin-bottom:8px;display:block;margin-left:auto;margin-right:auto">`
            : `<div style="width:64px;height:64px;border-radius:50%;background:var(--accent);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:bold;margin:0 auto 8px">${u.name[0].toUpperCase()}</div>`
          }
          <div>${u.name}</div>
        </div>
      `).join('')}
      <div class="card" style="text-align:center;padding:20px;cursor:pointer;min-width:100px"
           onclick="window.showNewProfileForm()">
        <div style="width:64px;height:64px;border-radius:50%;border:2px dashed var(--border);display:flex;align-items:center;justify-content:center;font-size:32px;margin:0 auto 8px">+</div>
        <div class="muted">New Profile</div>
      </div>
    </div>
    <div id="new-profile-form" style="display:none;max-width:340px;margin:0 auto">
      <div class="card">
        <h3 style="margin-bottom:16px">Create Profile</h3>
        <input id="profile-name" placeholder="Your name"
               style="width:100%;padding:8px;background:var(--surface);border:1px solid var(--border);border-radius:6px;color:var(--text);margin-bottom:12px">
        <label class="muted" style="display:block;margin-bottom:6px">Profile photo (optional)</label>
        <input type="file" id="avatar-input" accept="image/*" style="margin-bottom:16px;color:var(--text)">
        <button class="btn btn-primary" style="width:100%" onclick="window.createProfile()">Create</button>
      </div>
    </div>
  `;
}

window.selectUser = function(id, name) {
  sessionStorage.setItem('userId', id);
  sessionStorage.setItem('userName', name);
  document.querySelector('.top-nav').style.display = '';
  if (!sessionStorage.getItem('currentLanguage')) {
    renderLanguagePicker();
  } else {
    navigate(window.location.hash || '#home');
  }
};

window.showNewProfileForm = function() {
  document.getElementById('new-profile-form').style.display = 'block';
};

window.createProfile = async function() {
  const name = document.getElementById('profile-name').value.trim();
  if (!name) return;
  const res = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  const user = await res.json();
  const avatarInput = document.getElementById('avatar-input');
  if (avatarInput.files[0]) {
    const form = new FormData();
    form.append('avatar', avatarInput.files[0]);
    await fetch(`/api/users/${user.id}/avatar`, { method: 'POST', body: form });
  }
  window.selectUser(user.id, user.name);
};
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass (backend unchanged by this task).

- [ ] **Step 3: Commit**

```bash
git add frontend/js/users.js
git commit -m "feat: user picker screen with profile creation and avatar upload"
git push
```

---

## Task 11: Frontend languages.js

**Files:**
- Create: `frontend/js/languages.js`

**Context:** This file owns the language picker screen. Called from `app.js` startup (no language set) and from the 🌐 nav button. Hides the nav during selection. After picking, sets `sessionStorage.currentLanguage`, shows nav, and navigates to `#home`. The `navigate` function is defined in `app.js` — it's safe to call because by the time the user can click, `app.js` has loaded and set everything up.

- [ ] **Step 1: Create `frontend/js/languages.js`**

```javascript
async function renderLanguagePicker() {
  document.querySelector('.top-nav').style.display = 'none';
  const app = document.getElementById('app');
  const languages = await fetch('/api/languages').then(r => r.json());
  const userName = sessionStorage.getItem('userName') || 'there';

  if (languages.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px;margin-top:40px">
        <p class="muted">No language content found on the server.</p>
        <p class="muted" style="margin-top:8px;font-size:13px">Drop lesson folders into /data/lessons/ and restart.</p>
      </div>
    `;
    document.querySelector('.top-nav').style.display = '';
    return;
  }

  app.innerHTML = `
    <div style="text-align:center;padding:40px 0 20px">
      <h2>What would you like to learn?</h2>
      <p class="muted" style="margin-top:4px">Hi ${userName}! Pick a language to continue.</p>
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:16px;justify-content:center">
      ${languages.map(l => {
        const parts = l.label.split(' ');
        const flag = parts[0];
        const name = parts.slice(1).join(' ');
        return `
          <div class="card" style="text-align:center;padding:28px 24px;cursor:pointer;min-width:140px"
               onclick="window.selectLanguage('${l.language}')">
            <div style="font-size:48px;margin-bottom:8px">${flag}</div>
            <h3>${name}</h3>
            <p class="muted" style="margin-top:4px">${l.lesson_count} lessons</p>
          </div>
        `;
      }).join('')}
    </div>
  `;
}

window.selectLanguage = function(language) {
  sessionStorage.setItem('currentLanguage', language);
  document.querySelector('.top-nav').style.display = '';
  navigate('#home');
};
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/languages.js
git commit -m "feat: language picker screen with auto-discovered languages"
git push
```

---

## Task 12: Frontend app.js — Session Helpers + Startup Gating

**Files:**
- Modify: `frontend/js/app.js`

**Context:** `app.js` gains three sessionStorage helpers (`getCurrentUser`, `getCurrentLanguage`, `window.apiParams`), a `switchUser` function, and a new `init()` function that gates app entry on user and language being set. The existing `navigate` function and `renderLessons` function are unchanged except `renderLessons` now uses `apiParams()`. The `window.switchUser` function clears sessionStorage and re-renders the user picker. `renderLanguagePicker` (from `languages.js`) is called directly in `selectUser` when no language set — since `languages.js` is loaded before `app.js`, that function is already defined.

- [ ] **Step 1: Replace `frontend/js/app.js`**

```javascript
// --- Session helpers ---
function getCurrentUser() {
  return { id: sessionStorage.getItem('userId'), name: sessionStorage.getItem('userName') };
}

function getCurrentLanguage() {
  return sessionStorage.getItem('currentLanguage') || 'japanese';
}

window.apiParams = function() {
  return `user_id=${getCurrentUser().id}&language=${getCurrentLanguage()}`;
};

window.switchUser = function() {
  sessionStorage.removeItem('userId');
  sessionStorage.removeItem('userName');
  sessionStorage.removeItem('currentLanguage');
  renderUserPicker();
};

// --- Pages registry ---
const pages = {
  home: renderDashboard,
  lessons: renderLessons,
  review: renderReview,
  speak: renderSpeak,
};

// --- Lessons list page ---
async function renderLessons() {
  const app = document.getElementById('app');
  const lessons = await fetch('/api/lessons?' + window.apiParams()).then(r => r.json());
  const byUnit = {};
  for (const l of lessons) {
    (byUnit[l.unit] = byUnit[l.unit] || []).push(l);
  }
  app.innerHTML = '<h2 style="margin-bottom:16px">Lessons</h2>' +
    Object.entries(byUnit).map(([unit, ls]) => `
      <div class="card" style="margin-bottom:12px">
        <div class="label">Unit ${unit}</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px">
          ${ls.map(l => `
            <button onclick="startLesson(${l.unit},${l.lesson})"
                    class="btn ${l.completed ? 'btn-secondary' : 'btn-primary'}">
              ${l.completed ? '✓' : ''} Lesson ${l.lesson}
            </button>
          `).join('')}
        </div>
      </div>
    `).join('');
}

window.startLesson = function(unit, lesson) {
  window.location.hash = `#lesson/${unit}/${lesson}`;
};

// --- Router ---
function navigate(hash) {
  const [page, ...params] = (hash.replace('#', '') || 'home').split('/');
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  const fn = pages[page];
  if (fn) fn(...params);
}

// --- Nav event handlers ---
document.getElementById('hamburger').addEventListener('click', () => {
  document.getElementById('mobile-menu').classList.toggle('open');
});

document.querySelectorAll('.nav-link[data-page]').forEach(a => {
  a.addEventListener('click', () => {
    document.getElementById('mobile-menu').classList.remove('open');
  });
});

window.addEventListener('hashchange', () => navigate(window.location.hash));

// --- Startup gating ---
function init() {
  const user = getCurrentUser();
  if (!user.id) {
    renderUserPicker();
    return;
  }
  if (!sessionStorage.getItem('currentLanguage')) {
    renderLanguagePicker();
    return;
  }
  navigate(window.location.hash);
}

init();
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/app.js
git commit -m "feat: app.js session helpers, startup user/language gating, switchUser"
git push
```

---

## Task 13: Frontend Page Updates

**Files:**
- Modify: `frontend/js/dashboard.js`
- Modify: `frontend/js/lesson.js`
- Modify: `frontend/js/review.js`
- Modify: `frontend/js/speak.js`

**Context:** Every `fetch` call in these four files needs `window.apiParams()` appended. Additionally, `lesson.js` needs ASL handling: (1) skip the speak phase (jump `currentPhase` from 0 to 2 via `showPhase`), (2) in `showIntroduce`, render `<video>` instead of character text when `language === 'asl'` and card has a `video` field, (3) hide TTS button and auto-play for ASL. The `window.apiParams()` helper is defined in `app.js` and available at call time (these functions are called only after app.js loads).

- [ ] **Step 1: Replace `frontend/js/dashboard.js`**

```javascript
async function renderDashboard() {
  const app = document.getElementById('app');
  const params = window.apiParams();
  const [lessons, due] = await Promise.all([
    fetch('/api/lessons?' + params).then(r => r.json()),
    fetch('/api/review/due?' + params).then(r => r.json()),
  ]);

  const completed = lessons.filter(l => l.completed);
  const next = lessons.find(l => !l.completed);

  const today = new Date().toDateString();
  let streak = parseInt(localStorage.getItem('streak') || '0');
  const lastVisit = localStorage.getItem('lastVisit');
  if (lastVisit !== today) {
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    streak = lastVisit === yesterday ? streak + 1 : 1;
    localStorage.setItem('streak', streak);
    localStorage.setItem('lastVisit', today);
  }

  const unitMap = {};
  for (const l of lessons) {
    if (!unitMap[l.unit]) unitMap[l.unit] = { total: 0, done: 0 };
    unitMap[l.unit].total++;
    if (l.completed) unitMap[l.unit].done++;
  }

  app.innerHTML = `
    <div style="text-align:center;padding:28px 0 20px">
      <h2>Welcome back</h2>
      <p class="muted" style="margin-top:4px">🔥 ${streak}-day streak · ${completed.length} lessons done</p>
    </div>
    <div style="display:flex;gap:12px;margin-bottom:20px">
      ${next ? `
        <button onclick="startLesson(${next.unit},${next.lesson})" class="btn btn-primary btn-lg" style="flex:1">
          ▶ Continue — Lesson ${next.lesson}
        </button>
      ` : '<div class="btn btn-secondary btn-lg" style="flex:1;justify-content:center">🎉 All lessons complete!</div>'}
      <button onclick="window.location.hash='#review'" class="btn btn-secondary btn-lg" style="min-width:120px">
        🃏 Review<br><span style="font-size:12px">${due.length} due</span>
      </button>
    </div>
    <div class="card" style="margin-bottom:12px">
      <div class="label">Progress</div>
      ${Object.entries(unitMap).map(([unit, { total, done }]) => `
        <div style="margin-top:10px">
          <div style="display:flex;justify-content:space-between;margin-bottom:4px">
            <span class="muted">Unit ${unit}</span>
            <span class="muted">${done}/${total}</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width:${total ? (done / total * 100) : 0}%"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
```

- [ ] **Step 2: Replace `frontend/js/review.js`**

Read the current `frontend/js/review.js` to verify the exact content, then replace it with the version below that adds `window.apiParams()` to both fetch calls:

```javascript
async function renderReview() {
  const app = document.getElementById('app');
  const params = window.apiParams();
  const cards = await fetch('/api/review/due?' + params).then(r => r.json());

  if (cards.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <p class="muted">No cards due for review.</p>
        <button class="btn btn-primary" style="margin-top:16px" onclick="window.location.hash='#home'">Home</button>
      </div>
    `;
    return;
  }

  let idx = 0;

  function showCard() {
    if (idx >= cards.length) {
      app.innerHTML = `
        <div class="card" style="text-align:center;padding:48px">
          <div style="font-size:48px">✓</div>
          <h2 style="margin-top:12px">Session complete!</h2>
          <p class="muted" style="margin-top:8px">${cards.length} cards reviewed</p>
          <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Done</button>
        </div>
      `;
      return;
    }
    const card = cards[idx];
    app.innerHTML = `
      <div class="flashcard" id="flashcard" onclick="window.flipCard()">
        <div class="flashcard-front">
          <div style="font-size:72px;color:var(--accent-light)">${card.character}</div>
          <p class="muted" style="margin-top:12px">Tap to reveal</p>
        </div>
        <div class="flashcard-back" style="display:none">
          <div style="font-size:48px;color:var(--accent-light)">${card.character}</div>
          <div style="font-size:20px;margin-top:8px">${card.romaji}</div>
          <div class="muted">${card.meaning}</div>
          <div class="recall-btns" style="margin-top:20px">
            <button class="btn" style="background:#f87171" onclick="window.rate(1)">Again</button>
            <button class="btn" style="background:var(--yellow)" onclick="window.rate(2)">Hard</button>
            <button class="btn btn-primary" onclick="window.rate(3)">Good</button>
            <button class="btn" style="background:var(--green)" onclick="window.rate(4)">Easy</button>
          </div>
        </div>
      </div>
      <p class="muted" style="text-align:right;margin-top:8px">${idx + 1} / ${cards.length}</p>
    `;
  }

  window.flipCard = function() {
    document.querySelector('.flashcard-front').style.display = 'none';
    document.querySelector('.flashcard-back').style.display = 'block';
    document.getElementById('flashcard').onclick = null;
  };

  window.rate = async function(score) {
    const userId = sessionStorage.getItem('userId');
    await fetch(`/api/review/update?user_id=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: cards[idx].id, score }),
    });
    idx++;
    showCard();
  };

  showCard();
}
```

- [ ] **Step 3: Replace `frontend/js/speak.js`**

```javascript
async function renderSpeak() {
  const app = document.getElementById('app');
  const params = window.apiParams();
  const lessons = await fetch('/api/lessons?' + params).then(r => r.json());
  const completed = lessons.filter(l => l.completed);

  if (completed.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <p class="muted">Complete at least one lesson to unlock speaking practice.</p>
        <button class="btn btn-primary" style="margin-top:16px" onclick="window.location.hash='#lessons'">Go to Lessons</button>
      </div>
    `;
    return;
  }

  const lang = sessionStorage.getItem('currentLanguage');
  const allCards = [];
  for (const l of completed) {
    const data = await fetch(`/api/lessons/${l.unit}/${l.lesson}?language=${lang}`).then(r => r.json());
    allCards.push(...data.cards);
  }

  let current = null;

  window.pickRandom = function() {
    current = allCards[Math.floor(Math.random() * allCards.length)];
    app.innerHTML = `
      <h2 style="margin-bottom:16px">Speaking Practice</h2>
      <div class="card" style="text-align:center;padding:32px">
        <div style="font-size:72px;color:var(--accent-light)">${current.character}</div>
        <div style="font-size:20px;margin-top:8px">${current.romaji}</div>
        <button class="btn btn-secondary" style="margin:16px auto;display:block" onclick="playTTS('${current.character}')">🔊 Hear it</button>
        <button class="mic-btn" id="mic-btn" onclick="doSpeakPractice()">🎤</button>
        <p class="muted" style="margin-top:8px">Tap to speak</p>
        <div id="result" style="margin-top:16px;min-height:28px"></div>
      </div>
      <button class="btn btn-secondary" style="display:block;margin:16px auto" onclick="pickRandom()">Next →</button>
    `;
  };

  window.doSpeakPractice = async function() {
    const btn = document.getElementById('mic-btn');
    const result = document.getElementById('result');
    btn.classList.add('recording');
    result.innerHTML = '<span class="muted">Listening…</span>';
    try {
      const blob = await recordAudio(3000);
      btn.classList.remove('recording');
      result.innerHTML = '<span class="muted">Processing…</span>';
      const data = await recognizeSpeech(blob, current.character);
      result.innerHTML = data.match
        ? `<span style="color:var(--green)">✓ "${data.text}"</span>`
        : `<span style="color:#f87171">Heard: "${data.text}"</span>`;
    } catch {
      btn.classList.remove('recording');
      result.innerHTML = '<span style="color:var(--yellow)">Mic unavailable</span>';
    }
  };

  pickRandom();
}
```

- [ ] **Step 4: Replace `frontend/js/lesson.js`**

```javascript
let lessonData = null;
let currentPhase = 0; // 0=introduce, 1=speak, 2=write, 3=quiz
let currentCardIdx = 0;
let quizResults = [];

async function renderLesson(unit, lesson) {
  if (!unit || !lesson) { window.location.hash = '#lessons'; return; }
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  lessonData = await fetch(`/api/lessons/${unit}/${lesson}?language=${lang}`).then(r => r.json());
  currentPhase = 0; currentCardIdx = 0; quizResults = [];
  showPhase();
}

function phaseBar() {
  return `<div class="phase-bar">
    ${['Introduce', 'Speak', 'Write', 'Quiz'].map((p, i) => `
      <div class="phase-dot ${i < currentPhase ? 'done' : i === currentPhase ? 'active' : ''}"></div>
    `).join('')}
  </div>`;
}

function showPhase() {
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  if (currentPhase === 0) showIntroduce();
  else if (currentPhase === 1) {
    if (lang === 'asl') { currentPhase = 2; showWrite(); }
    else showSpeak();
  }
  else if (currentPhase === 2) showWrite();
  else showQuiz();
}

function showIntroduce() {
  const card = lessonData.cards[currentCardIdx];
  const lang = sessionStorage.getItem('currentLanguage') || 'japanese';
  const isAsl = lang === 'asl';
  const mediaHtml = (isAsl && card.video)
    ? `<video src="/videos/asl/${card.video}" autoplay loop muted playsinline
              style="max-width:280px;max-height:280px;border-radius:8px;margin:0 auto;display:block"></video>`
    : `<div style="font-size:80px;color:var(--accent-light)">${card.character}</div>`;

  document.getElementById('app').innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:32px">
      ${mediaHtml}
      <div style="font-size:24px;margin-top:8px">${card.romaji}</div>
      <div class="muted" style="margin-top:4px">${card.meaning}</div>
      ${!isAsl ? `<button class="btn btn-secondary" style="margin-top:20px" onclick="playTTS('${card.character}')">🔊 Hear it</button>` : ''}
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextIntroduce()">Next →</button>
    </div>
  `;
  if (!isAsl) playTTS(card.character);
}

window.nextIntroduce = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showIntroduce();
  else { currentPhase = 1; currentCardIdx = 0; showPhase(); }
};

function showSpeak() {
  const card = lessonData.cards[currentCardIdx];
  const app = document.getElementById('app');
  app.innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:32px">
      <div style="font-size:64px;color:var(--accent-light)">${card.character}</div>
      <div style="font-size:20px;margin:8px 0">${card.romaji}</div>
      <button class="btn btn-secondary" style="margin-bottom:20px" onclick="playTTS('${card.character}')">🔊 Hear it</button>
      <div>
        <button class="mic-btn" id="mic-btn" onclick="doSpeak('${card.character}')">🎤</button>
        <p class="muted" style="margin-top:8px">Tap to speak</p>
      </div>
      <div id="stt-result" style="margin-top:16px;min-height:24px"></div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextSpeak()">Next →</button>
    </div>
  `;
}

window.doSpeak = async function(expected) {
  const btn = document.getElementById('mic-btn');
  const result = document.getElementById('stt-result');
  btn.classList.add('recording');
  result.innerHTML = '<span class="muted">Listening…</span>';
  try {
    const blob = await recordAudio(3000);
    btn.classList.remove('recording');
    result.innerHTML = '<span class="muted">Processing…</span>';
    const data = await recognizeSpeech(blob, expected);
    result.innerHTML = data.match
      ? `<span style="color:var(--green)">✓ Whisper heard: ${data.text}</span>`
      : `<span style="color:#f87171">✗ Whisper heard: "${data.text}" (expected: ${expected})</span>`;
  } catch {
    btn.classList.remove('recording');
    result.innerHTML = '<span style="color:var(--yellow)">Mic unavailable — tap Next to continue</span>';
  }
};

window.nextSpeak = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showSpeak();
  else { currentPhase = 2; currentCardIdx = 0; showWrite(); }
};

function showWrite() {
  const card = lessonData.cards[currentCardIdx];
  document.getElementById('app').innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:24px">
      <div class="muted" style="margin-bottom:8px">Draw: <strong>${card.romaji}</strong> (${card.meaning})</div>
      <canvas id="write-canvas" class="writing-canvas" width="280" height="280"></canvas>
      <div style="display:flex;gap:8px;justify-content:center;margin-top:12px">
        <button class="btn btn-secondary" onclick="clearCanvas()">Clear</button>
        <button class="btn btn-secondary" onclick="showHint('${card.character}')">Hint</button>
      </div>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextWrite()">Next →</button>
    </div>
  `;
  initCanvas();
}

function initCanvas() {
  const canvas = document.getElementById('write-canvas');
  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = '#93c5fd'; ctx.lineWidth = 3; ctx.lineCap = 'round';
  let drawing = false;

  const pos = (e) => {
    const r = canvas.getBoundingClientRect();
    const src = e.touches ? e.touches[0] : e;
    return [src.clientX - r.left, src.clientY - r.top];
  };

  canvas.addEventListener('mousedown', e => { drawing = true; ctx.beginPath(); ctx.moveTo(...pos(e)); });
  canvas.addEventListener('mousemove', e => { if (!drawing) return; ctx.lineTo(...pos(e)); ctx.stroke(); });
  canvas.addEventListener('mouseup', () => drawing = false);
  canvas.addEventListener('touchstart', e => { e.preventDefault(); drawing = true; ctx.beginPath(); ctx.moveTo(...pos(e)); }, { passive: false });
  canvas.addEventListener('touchmove', e => { e.preventDefault(); if (!drawing) return; ctx.lineTo(...pos(e)); ctx.stroke(); }, { passive: false });
  canvas.addEventListener('touchend', () => drawing = false);
}

window.clearCanvas = function() {
  const c = document.getElementById('write-canvas');
  c.getContext('2d').clearRect(0, 0, c.width, c.height);
};

window.showHint = function(char) {
  const c = document.getElementById('write-canvas');
  const ctx = c.getContext('2d');
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.font = '200px serif'; ctx.fillStyle = 'rgba(147,197,253,0.15)';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(char, 140, 140);
};

window.nextWrite = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showWrite();
  else { currentPhase = 3; showQuiz(); }
};

function showQuiz() {
  const cards = lessonData.cards;
  const questions = [...cards].sort(() => Math.random() - 0.5).slice(0, Math.min(5, cards.length));
  let qIdx = 0;

  function showQuestion() {
    if (qIdx >= questions.length) { showQuizResults(); return; }
    const q = questions[qIdx];
    const distractors = cards.filter(c => c.id !== q.id).sort(() => Math.random() - 0.5).slice(0, Math.min(3, cards.length - 1));
    const options = [...distractors, q].sort(() => Math.random() - 0.5);

    document.getElementById('app').innerHTML = `
      ${phaseBar()}
      <div class="card" style="text-align:center;padding:24px">
        <p class="muted">Which character makes this sound?</p>
        <div style="font-size:32px;margin:16px 0">${q.romaji}</div>
        <div class="quiz-options">
          ${options.map(o => `
            <div class="quiz-opt" onclick="checkAnswer(this,'${o.character}','${q.character}')">
              ${o.character}
            </div>
          `).join('')}
        </div>
      </div>
      <div style="text-align:right;margin-top:12px">
        <span class="muted">${qIdx + 1} / ${questions.length}</span>
      </div>
    `;
  }

  window.checkAnswer = function(el, chosen, correct) {
    document.querySelectorAll('.quiz-opt').forEach(o => o.onclick = null);
    if (chosen === correct) {
      el.classList.add('correct');
      quizResults.push(true);
    } else {
      el.classList.add('wrong');
      document.querySelectorAll('.quiz-opt').forEach(o => {
        if (o.textContent.trim() === correct) o.classList.add('correct');
      });
      quizResults.push(false);
    }
    setTimeout(() => { qIdx++; showQuestion(); }, 900);
  };

  showQuestion();
}

async function showQuizResults() {
  const correct = quizResults.filter(Boolean).length;
  const score = `${correct}/${quizResults.length}`;
  await fetch(
    `/api/lessons/${lessonData.unit}/${lessonData.lesson}/complete?${window.apiParams()}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quiz_score: score }),
    }
  );
  document.getElementById('app').innerHTML = `
    <div class="card" style="text-align:center;padding:40px">
      <div style="font-size:48px">${correct === quizResults.length ? '🎉' : '📝'}</div>
      <h2 style="margin-top:12px">Lesson Complete!</h2>
      <p class="muted" style="margin-top:8px">Score: ${score}</p>
      <div style="display:flex;gap:12px;justify-content:center;margin-top:24px">
        <button class="btn btn-secondary" onclick="window.location.hash='#home'">Home</button>
        <button class="btn btn-primary" onclick="window.location.hash='#lessons'">Next Lesson</button>
      </div>
    </div>
  `;
}

if (typeof pages !== 'undefined') pages.lesson = renderLesson;
```

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/js/dashboard.js frontend/js/lesson.js frontend/js/review.js frontend/js/speak.js
git commit -m "feat: all page components use apiParams(), lesson.js handles ASL phase skip and video"
git push
```

---

## Self-Review

**1. Spec coverage check:**
- ✅ Lesson files reorganized to `lessons/japanese/` — Task 1
- ✅ `users` table, `language` on `cards`, `user_id`/`language` on `progress`/`lessons` — Task 2
- ✅ Migration assigns existing rows to "Player 1" — Task 2 (`_migrate_progress`, `_migrate_lessons`)
- ✅ Avatar stored as JPEG at `/data/avatars/{id}.jpg` via Pillow — Task 4
- ✅ `/avatars` and `/videos` static mounts — Task 4 (`main.py`)
- ✅ `GET /api/languages` scans lessons dir, returns label + count — Task 5
- ✅ Seed extracts language from folder path — Task 6
- ✅ All lesson endpoints require user_id + language — Task 7
- ✅ All review endpoints require user_id — Task 8
- ✅ User picker screen with profile creation — Task 10
- ✅ Language picker screen — Task 11
- ✅ `switchUser` clears session and re-shows picker — Task 12
- ✅ Language switcher nav button — Task 9
- ✅ `apiParams()` on all fetch calls — Task 13
- ✅ ASL: video in introduce, speak phase skipped — Task 13 (`lesson.js`)
- ✅ ASL: TTS hidden — Task 13 (`lesson.js`)
- ✅ Language labels mapping (japanese/spanish/asl) — Task 5

**2. Type consistency check:**
- `window.apiParams()` defined in `app.js` (Task 12), used in `dashboard.js`, `lesson.js`, `review.js`, `speak.js` (Task 13) ✅
- `renderUserPicker` defined in `users.js` (Task 10), called from `app.js` (Task 12) ✅
- `renderLanguagePicker` defined in `languages.js` (Task 11), called from `app.js` and `users.js` ✅
- `navigate` defined in `app.js` (Task 12), called from `languages.js` (Task 11) and `users.js` (Task 10) ✅ — safe because called at runtime, not definition time
- DB DDL `CREATE_USERS` exported from `database.py` (Task 2), imported in `conftest.py` (Task 2) and test fixtures ✅
- `language` column on `cards` table used in `lessons.py` (Task 7), `progress.py` (Task 8), `seed.py` (Task 6) ✅
