# Japanese Learning App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal Japanese learning web app with structured lessons, SRS review, and spoken/written practice, running in Docker on a home Linux server.

**Architecture:** FastAPI serves both REST API and vanilla HTML/JS/CSS frontend. Whisper handles local STT; edge-tts handles TTS with MP3 caching. SQLite stores all progress via host bind mounts. Caddy (user-managed) terminates HTTPS.

**Tech Stack:** Python 3.11, FastAPI, aiosqlite, openai-whisper, edge-tts, pydantic-settings, python-multipart, httpx, pytest, pytest-asyncio; Docker + Docker Compose; Vanilla HTML/CSS/JS (no build step).

---

## File Structure

```
Learning_Japanese/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, startup hooks, static mount
│   ├── config.py            # Settings from env (DATA_DIR, PORT, etc.)
│   ├── database.py          # DB path, table DDL, get_db dependency, init_db
│   ├── models.py            # Pydantic request/response models
│   ├── seed.py              # Copy bundled lessons → /data/lessons, seed cards table
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── lessons.py       # GET /api/lessons, GET /api/lessons/{u}/{l}, POST complete
│   │   ├── progress.py      # GET /api/review/due, POST /api/review/update
│   │   └── speech.py        # GET /api/speech/tts, POST /api/speech/recognize
│   └── services/
│       ├── __init__.py
│       ├── srs.py           # SM-2 algorithm (pure functions, no I/O)
│       ├── tts.py           # edge-tts wrapper with MP3 cache
│       └── stt.py           # Whisper wrapper (lazy model load)
├── frontend/
│   ├── index.html           # App shell, top nav
│   ├── css/
│   │   └── main.css         # Dark theme, responsive
│   └── js/
│       ├── app.js           # Hash router, nav link handling
│       ├── audio.js         # Mic recording + TTS playback helpers
│       ├── dashboard.js     # Home page
│       ├── lesson.js        # 4-phase lesson flow
│       ├── review.js        # SRS flashcard session
│       └── speak.js         # Freeform speaking practice
├── lessons/
│   ├── unit1/               # Hiragana (lesson01–20.json)
│   └── unit2/               # Katakana (lesson01–20.json)
├── tests/
│   ├── conftest.py
│   ├── test_srs.py
│   ├── test_database.py
│   ├── test_seed.py
│   ├── test_lessons.py
│   ├── test_progress.py
│   └── test_speech.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `app/__init__.py`, `app/routers/__init__.py`, `app/services/__init__.py`
- Create: `app/config.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p app/routers app/services frontend/css frontend/js lessons/unit1 lessons/unit2 tests
touch app/__init__.py app/routers/__init__.py app/services/__init__.py
```

- [ ] **Step 2: Create `requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
aiosqlite==0.20.0
pydantic-settings==2.2.1
edge-tts==6.1.9
openai-whisper==20231117
python-multipart==0.0.9
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 3: Create `.env.example`**

```
DATA_DIR=/data
CONFIG_DIR=/config
PORT=13200
```

- [ ] **Step 4: Create `app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    data_dir: str = "/data"
    config_dir: str = "/config"
    port: int = 13200

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 5: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without error.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .env.example app/
git commit -m "feat: project scaffold and config"
```

---

## Task 2: Database Setup

**Files:**
- Create: `app/database.py`
- Create: `app/models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_database.py
import pytest
import pytest_asyncio
import aiosqlite

@pytest.mark.asyncio
async def test_init_db_creates_tables(tmp_path, monkeypatch):
    monkeypatch.setattr("app.database.get_db_path", lambda: tmp_path / "test.db")
    from app.database import init_db
    await init_db()
    async with aiosqlite.connect(tmp_path / "test.db") as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in await cursor.fetchall()}
    assert {"cards", "progress", "lessons"} == tables
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
pytest tests/test_database.py -v
```

Expected: `FAILED` — `app.database` not found.

- [ ] **Step 3: Create `app/database.py`**

```python
from pathlib import Path
import aiosqlite
from app.config import settings

def get_db_path() -> Path:
    return Path(settings.data_dir) / "progress.db"

CREATE_CARDS = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    character TEXT NOT NULL,
    romaji TEXT NOT NULL,
    meaning TEXT NOT NULL,
    unit INTEGER NOT NULL,
    lesson INTEGER NOT NULL,
    audio_path TEXT
)
"""

CREATE_PROGRESS = """
CREATE TABLE IF NOT EXISTS progress (
    card_id INTEGER PRIMARY KEY REFERENCES cards(id),
    due_date DATE NOT NULL,
    interval_days INTEGER NOT NULL DEFAULT 1,
    ease_factor REAL NOT NULL DEFAULT 2.5,
    review_count INTEGER NOT NULL DEFAULT 0,
    last_score INTEGER
)
"""

CREATE_LESSONS = """
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER NOT NULL,
    unit INTEGER NOT NULL,
    completed_at DATETIME,
    quiz_score TEXT,
    PRIMARY KEY (lesson_id, unit)
)
"""

async def init_db():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()

async def get_db():
    async with aiosqlite.connect(get_db_path()) as db:
        db.row_factory = aiosqlite.Row
        yield db
```

- [ ] **Step 4: Create `app/models.py`**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ReviewUpdate(BaseModel):
    card_id: int
    score: int  # 1–4

class LessonComplete(BaseModel):
    quiz_score: str  # e.g. "4/5"

class TranscriptionResult(BaseModel):
    text: str
    expected: str
    match: bool
```

- [ ] **Step 5: Create `tests/conftest.py`**

```python
import pytest
import pytest_asyncio
import aiosqlite
from httpx import AsyncClient, ASGITransport

from app.database import CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS, get_db

@pytest_asyncio.fixture
async def test_db(tmp_path):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()
        yield db

@pytest_asyncio.fixture
async def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    async with aiosqlite.connect(db_path) as setup_db:
        await setup_db.execute(CREATE_CARDS)
        await setup_db.execute(CREATE_PROGRESS)
        await setup_db.execute(CREATE_LESSONS)
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

- [ ] **Step 6: Run tests**

```bash
pytest tests/test_database.py -v
```

Expected: `PASSED`.

- [ ] **Step 7: Commit**

```bash
git add app/database.py app/models.py tests/
git commit -m "feat: database schema and test fixtures"
```

---

## Task 3: SRS Service

**Files:**
- Create: `app/services/srs.py`
- Create: `tests/test_srs.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_srs.py
from app.services.srs import SRSCard, next_interval, due_date
from datetime import date, timedelta

def test_score_below_2_resets_interval():
    card = SRSCard(interval_days=10, ease_factor=2.5, review_count=5)
    result = next_interval(card, score=1)
    assert result.interval_days == 1

def test_first_review_gives_interval_1():
    card = SRSCard(interval_days=1, ease_factor=2.5, review_count=0)
    result = next_interval(card, score=3)
    assert result.interval_days == 1
    assert result.review_count == 1

def test_second_review_gives_interval_6():
    card = SRSCard(interval_days=1, ease_factor=2.5, review_count=1)
    result = next_interval(card, score=3)
    assert result.interval_days == 6

def test_subsequent_review_multiplies_by_ease():
    card = SRSCard(interval_days=6, ease_factor=2.5, review_count=2)
    result = next_interval(card, score=3)
    assert result.interval_days == 15  # round(6 * 2.5)

def test_ease_decreases_on_hard():
    card = SRSCard(interval_days=6, ease_factor=2.5, review_count=2)
    result = next_interval(card, score=2)
    assert result.ease_factor < 2.5

def test_ease_never_below_1_3():
    card = SRSCard(interval_days=1, ease_factor=1.3, review_count=3)
    result = next_interval(card, score=1)
    assert result.ease_factor >= 1.3

def test_due_date_is_today_plus_interval():
    d = due_date(3)
    assert d == date.today() + timedelta(days=3)
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_srs.py -v
```

Expected: `FAILED` — module not found.

- [ ] **Step 3: Create `app/services/srs.py`**

```python
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class SRSCard:
    interval_days: int
    ease_factor: float
    review_count: int

def next_interval(card: SRSCard, score: int) -> SRSCard:
    """SM-2 algorithm. score: 1=blackout, 2=hard, 3=good, 4=easy."""
    new_ease = max(1.3, card.ease_factor + (0.1 - (4 - score) * (0.08 + (4 - score) * 0.02)))

    if score < 2:
        return SRSCard(interval_days=1, ease_factor=card.ease_factor, review_count=card.review_count + 1)

    if card.review_count == 0:
        new_interval = 1
    elif card.review_count == 1:
        new_interval = 6
    else:
        new_interval = round(card.interval_days * new_ease)

    return SRSCard(interval_days=new_interval, ease_factor=new_ease, review_count=card.review_count + 1)

def due_date(interval_days: int) -> date:
    return date.today() + timedelta(days=interval_days)
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_srs.py -v
```

Expected: All 7 tests `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/services/srs.py tests/test_srs.py
git commit -m "feat: SM-2 SRS algorithm"
```

---

## Task 4: Lesson JSON Content — Unit 1 Hiragana

**Files:**
- Create: `lessons/unit1/lesson01.json` through `lesson20.json`

Each file follows this schema:
```json
{
  "unit": 1,
  "lesson": 1,
  "title": "Hiragana — Vowels (あ行)",
  "cards": [
    {"type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel 'a' as in father"}
  ]
}
```

- [ ] **Step 1: Create `lessons/unit1/lesson01.json`**

```json
{
  "unit": 1, "lesson": 1, "title": "Hiragana — Vowels (あ行)",
  "cards": [
    {"type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel 'a' as in father"},
    {"type": "hiragana", "character": "い", "romaji": "i", "meaning": "vowel 'i' as in feet"},
    {"type": "hiragana", "character": "う", "romaji": "u", "meaning": "vowel 'u' as in moon"},
    {"type": "hiragana", "character": "え", "romaji": "e", "meaning": "vowel 'e' as in red"},
    {"type": "hiragana", "character": "お", "romaji": "o", "meaning": "vowel 'o' as in go"}
  ]
}
```

- [ ] **Step 2: Create `lessons/unit1/lesson02.json`**

```json
{
  "unit": 1, "lesson": 2, "title": "Hiragana — K-row (か行)",
  "cards": [
    {"type": "hiragana", "character": "か", "romaji": "ka", "meaning": "ka"},
    {"type": "hiragana", "character": "き", "romaji": "ki", "meaning": "ki"},
    {"type": "hiragana", "character": "く", "romaji": "ku", "meaning": "ku"},
    {"type": "hiragana", "character": "け", "romaji": "ke", "meaning": "ke"},
    {"type": "hiragana", "character": "こ", "romaji": "ko", "meaning": "ko"}
  ]
}
```

- [ ] **Step 3: Create `lessons/unit1/lesson03.json`**

```json
{
  "unit": 1, "lesson": 3, "title": "Hiragana — S-row (さ行)",
  "cards": [
    {"type": "hiragana", "character": "さ", "romaji": "sa", "meaning": "sa"},
    {"type": "hiragana", "character": "し", "romaji": "shi", "meaning": "shi"},
    {"type": "hiragana", "character": "す", "romaji": "su", "meaning": "su"},
    {"type": "hiragana", "character": "せ", "romaji": "se", "meaning": "se"},
    {"type": "hiragana", "character": "そ", "romaji": "so", "meaning": "so"}
  ]
}
```

- [ ] **Step 4: Create lessons 04–10 (T, N, H, M, Y, R, W rows)**

Create each file using the same schema. Content:

| File | Title | Characters |
|---|---|---|
| `lesson04.json` | T-row (た行) | た=ta, ち=chi, つ=tsu, て=te, と=to |
| `lesson05.json` | N-row (な行) | な=na, に=ni, ぬ=nu, ね=ne, の=no |
| `lesson06.json` | H-row (は行) | は=ha, ひ=hi, ふ=fu, へ=he, ほ=ho |
| `lesson07.json` | M-row (ま行) | ま=ma, み=mi, む=mu, め=me, も=mo |
| `lesson08.json` | Y-row (や行) | や=ya, ゆ=yu, よ=yo |
| `lesson09.json` | R-row (ら行) | ら=ra, り=ri, る=ru, れ=re, ろ=ro |
| `lesson10.json` | W-row + N (わ行) | わ=wa, を=wo (object marker), ん=n (syllabic nasal) |

- [ ] **Step 5: Create lessons 11–15 (dakuten and handakuten)**

| File | Title | Characters |
|---|---|---|
| `lesson11.json` | G-row (が行) | が=ga, ぎ=gi, ぐ=gu, げ=ge, ご=go |
| `lesson12.json` | Z-row (ざ行) | ざ=za, じ=ji, ず=zu, ぜ=ze, ぞ=zo |
| `lesson13.json` | D-row (だ行) | だ=da, ぢ=ji (rare), づ=zu (rare), で=de, ど=do |
| `lesson14.json` | B-row (ば行) | ば=ba, び=bi, ぶ=bu, べ=be, ぼ=bo |
| `lesson15.json` | P-row (ぱ行) | ぱ=pa, ぴ=pi, ぷ=pu, ぺ=pe, ぽ=po |

- [ ] **Step 6: Create lessons 16–20 (combination characters)**

| File | Title | Characters |
|---|---|---|
| `lesson16.json` | KI+SHI combos | きゃ=kya, きゅ=kyu, きょ=kyo, しゃ=sha, しゅ=shu, しょ=sho |
| `lesson17.json` | CHI+NI combos | ちゃ=cha, ちゅ=chu, ちょ=cho, にゃ=nya, にゅ=nyu, にょ=nyo |
| `lesson18.json` | HI+MI combos | ひゃ=hya, ひゅ=hyu, ひょ=hyo, みゃ=mya, みゅ=myu, みょ=myo |
| `lesson19.json` | RI combos | りゃ=rya, りゅ=ryu, りょ=ryo |
| `lesson20.json` | Voiced combos | ぎゃ=gya, ぎゅ=gyu, ぎょ=gyo, じゃ=ja, じゅ=ju, じょ=jo, びゃ=bya, びゅ=byu, びょ=byo, ぴゃ=pya, ぴゅ=pyu, ぴょ=pyo |

- [ ] **Step 7: Commit**

```bash
git add lessons/unit1/
git commit -m "feat: Unit 1 hiragana lesson content (20 lessons)"
```

---

## Task 5: Seed Service

**Files:**
- Create: `app/seed.py`
- Create: `tests/test_seed.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_seed.py
import json
import pytest
import pytest_asyncio
import aiosqlite
from pathlib import Path
from app.database import CREATE_CARDS, CREATE_PROGRESS, CREATE_LESSONS

@pytest_asyncio.fixture
async def seeded_db(tmp_path):
    # Create minimal lesson JSON
    lesson_dir = tmp_path / "lessons" / "unit1"
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "lesson01.json").write_text(json.dumps({
        "unit": 1, "lesson": 1, "title": "Test",
        "cards": [
            {"type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel a"}
        ]
    }))
    db_path = tmp_path / "progress.db"
    async with aiosqlite.connect(db_path) as db:
        await db.execute(CREATE_CARDS)
        await db.execute(CREATE_PROGRESS)
        await db.execute(CREATE_LESSONS)
        await db.commit()
    return tmp_path

@pytest.mark.asyncio
async def test_seed_inserts_cards(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.database.get_db_path", lambda: seeded_db / "progress.db")
    from app.seed import seed_if_empty
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
    assert count == 1

@pytest.mark.asyncio
async def test_seed_is_idempotent(seeded_db, monkeypatch):
    monkeypatch.setattr("app.seed.DATA_DIR", seeded_db)
    monkeypatch.setattr("app.database.get_db_path", lambda: seeded_db / "progress.db")
    from app.seed import seed_if_empty
    await seed_if_empty()
    await seed_if_empty()
    async with aiosqlite.connect(seeded_db / "progress.db") as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
    assert count == 1
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_seed.py -v
```

Expected: `FAILED`.

- [ ] **Step 3: Create `app/seed.py`**

```python
import json
import shutil
from pathlib import Path
import aiosqlite
from app.config import settings
from app.database import get_db_path

DATA_DIR = Path(settings.data_dir)
BUNDLED_LESSONS = Path(__file__).parent.parent / "lessons"

async def seed_if_empty():
    lessons_dir = DATA_DIR / "lessons"
    # Copy bundled lessons to data volume on first run
    if not lessons_dir.exists() or not any(lessons_dir.rglob("*.json")):
        shutil.copytree(BUNDLED_LESSONS, lessons_dir, dirs_exist_ok=True)

    async with aiosqlite.connect(get_db_path()) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM cards")
        count = (await cursor.fetchone())[0]
        if count > 0:
            return
        for lesson_file in sorted(lessons_dir.rglob("lesson*.json")):
            data = json.loads(lesson_file.read_text(encoding="utf-8"))
            for card in data["cards"]:
                await db.execute(
                    "INSERT INTO cards (type, character, romaji, meaning, unit, lesson) VALUES (?,?,?,?,?,?)",
                    (card["type"], card["character"], card["romaji"],
                     card["meaning"], data["unit"], data["lesson"])
                )
        await db.commit()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_seed.py -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/seed.py tests/test_seed.py
git commit -m "feat: lesson seed service with idempotent first-run copy"
```

---

## Task 6: TTS Service

**Files:**
- Create: `app/services/tts.py`
- Create: `tests/test_tts.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tts.py
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_get_audio_returns_path(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = AsyncMock()
    with patch("edge_tts.Communicate", return_value=mock_comm):
        from app.services.tts import get_audio
        path = await get_audio("あ")
    assert path.suffix == ".mp3"
    assert path.parent == tmp_path

@pytest.mark.asyncio
async def test_get_audio_caches(tmp_path, monkeypatch):
    monkeypatch.setattr("app.services.tts.AUDIO_DIR", tmp_path)
    mock_comm = MagicMock()
    mock_comm.save = AsyncMock()
    with patch("edge_tts.Communicate", return_value=mock_comm) as mock_cls:
        from app.services.tts import get_audio
        await get_audio("あ")
        # Create the file so cache check passes
        (tmp_path / list(tmp_path.glob("*.mp3"))[0].name).touch()
        await get_audio("あ")
    assert mock_cls.call_count == 1
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_tts.py -v
```

Expected: `FAILED`.

- [ ] **Step 3: Create `app/services/tts.py`**

```python
import hashlib
from pathlib import Path
import edge_tts
from app.config import settings

AUDIO_DIR = Path(settings.data_dir) / "audio"
VOICE = "ja-JP-NanamiNeural"

async def get_audio(text: str) -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(text.encode()).hexdigest()
    path = AUDIO_DIR / f"{key}.mp3"
    if not path.exists():
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(str(path))
    return path
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_tts.py -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/services/tts.py tests/test_tts.py
git commit -m "feat: TTS service with MP3 caching"
```

---

## Task 7: STT Service

**Files:**
- Create: `app/services/stt.py`
- Create: `tests/test_stt.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stt.py
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_transcribe_returns_text():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": " あ "}
    with patch("app.services.stt.get_model", return_value=mock_model):
        from app.services.stt import transcribe
        result = await transcribe(b"fake_audio", suffix=".wav")
    assert result == "あ"

@pytest.mark.asyncio
async def test_transcribe_strips_whitespace():
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "  か  "}
    with patch("app.services.stt.get_model", return_value=mock_model):
        from app.services.stt import transcribe
        result = await transcribe(b"fake_audio")
    assert result == "か"
```

- [ ] **Step 2: Run to confirm failure**

```bash
pytest tests/test_stt.py -v
```

Expected: `FAILED`.

- [ ] **Step 3: Create `app/services/stt.py`**

```python
import asyncio
import tempfile
from pathlib import Path

_model = None

def get_model():
    global _model
    if _model is None:
        import whisper
        _model = whisper.load_model("base")
    return _model

async def transcribe(audio_bytes: bytes, suffix: str = ".webm") -> str:
    model = get_model()
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    result = await asyncio.to_thread(
        model.transcribe, tmp_path, language="ja", fp16=False
    )
    Path(tmp_path).unlink(missing_ok=True)
    return result["text"].strip()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_stt.py -v
```

Expected: `PASSED`.

- [ ] **Step 5: Commit**

```bash
git add app/services/stt.py tests/test_stt.py
git commit -m "feat: STT service with local Whisper (lazy load)"
```

---

## Task 8: API Routers

**Files:**
- Create: `app/routers/lessons.py`
- Create: `app/routers/progress.py`
- Create: `app/routers/speech.py`
- Create: `tests/test_lessons.py`
- Create: `tests/test_progress.py`
- Create: `tests/test_speech.py`

- [ ] **Step 1: Write failing tests for lessons router**

```python
# tests/test_lessons.py
import pytest

@pytest.mark.asyncio
async def test_list_lessons_empty(client):
    response = await client.get("/api/lessons")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_lesson_not_found(client):
    response = await client.get("/api/lessons/1/1")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_complete_lesson_adds_to_progress(client):
    # Insert a card directly via the DB
    from app.database import get_db
    async for db in client.app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson) VALUES (?,?,?,?,?,?)",
            ("hiragana","あ","a","vowel a",1,1)
        )
        await db.commit()
        break
    response = await client.post("/api/lessons/1/1/complete", json={"quiz_score": "5/5"})
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Create `app/routers/lessons.py`**

```python
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
```

- [ ] **Step 3: Write failing tests for progress router**

```python
# tests/test_progress.py
import pytest

@pytest.mark.asyncio
async def test_due_cards_empty(client):
    response = await client.get("/api/review/due")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_update_progress(client):
    from app.database import get_db
    async for db in client.app.dependency_overrides[get_db]():
        await db.execute(
            "INSERT INTO cards (type,character,romaji,meaning,unit,lesson) VALUES (?,?,?,?,?,?)",
            ("hiragana","あ","a","vowel a",1,1)
        )
        await db.execute(
            "INSERT INTO progress (card_id, due_date, interval_days, ease_factor, review_count)"
            " VALUES (1, date('now'), 1, 2.5, 0)"
        )
        await db.commit()
        break
    response = await client.post("/api/review/update", json={"card_id": 1, "score": 3})
    assert response.status_code == 200
    data = response.json()
    assert "due_date" in data
    assert data["interval_days"] == 1
```

- [ ] **Step 4: Create `app/routers/progress.py`**

```python
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
```

- [ ] **Step 5: Write failing tests for speech router**

```python
# tests/test_speech.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

@pytest.mark.asyncio
async def test_tts_returns_audio(client, tmp_path):
    fake_mp3 = tmp_path / "test.mp3"
    fake_mp3.write_bytes(b"fake mp3 data")
    with patch("app.routers.speech.get_audio", new=AsyncMock(return_value=fake_mp3)):
        response = await client.get("/api/speech/tts?text=%E3%81%82")
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"

@pytest.mark.asyncio
async def test_recognize_returns_transcription(client):
    with patch("app.routers.speech.transcribe", new=AsyncMock(return_value="あ")):
        response = await client.post(
            "/api/speech/recognize?expected=%E3%81%82",
            files={"audio": ("audio.wav", b"fake", "audio/wav")}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "あ"
    assert data["match"] is True
```

- [ ] **Step 6: Create `app/routers/speech.py`**

```python
import asyncio
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import FileResponse
from app.services.tts import get_audio
from app.services.stt import transcribe

router = APIRouter(prefix="/api/speech", tags=["speech"])

@router.get("/tts")
async def text_to_speech(text: str = Query(...)):
    path = await get_audio(text)
    return FileResponse(str(path), media_type="audio/mpeg")

@router.post("/recognize")
async def speech_to_text(
    audio: UploadFile = File(...),
    expected: str = Query(default="")
):
    audio_bytes = await audio.read()
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    try:
        text = await asyncio.wait_for(transcribe(audio_bytes, suffix), timeout=10.0)
    except asyncio.TimeoutError:
        return {"error": "timeout", "text": "", "expected": expected, "match": False}
    return {"text": text, "expected": expected, "match": text == expected}
```

- [ ] **Step 7: Run all router tests**

```bash
pytest tests/test_lessons.py tests/test_progress.py tests/test_speech.py -v
```

Expected: All tests `PASSED`.

- [ ] **Step 8: Commit**

```bash
git add app/routers/ tests/test_lessons.py tests/test_progress.py tests/test_speech.py
git commit -m "feat: API routers for lessons, progress, and speech"
```

---

## Task 9: FastAPI Main App

**Files:**
- Create: `app/main.py`

- [ ] **Step 1: Create `app/main.py`**

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

app = FastAPI(title="Japanese Learning App")

app.include_router(lessons_router)
app.include_router(progress_router)
app.include_router(speech_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

@app.on_event("startup")
async def startup():
    await init_db()
    await seed_if_empty()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=False)
```

- [ ] **Step 2: Create placeholder `frontend/index.html` so static mount doesn't error**

```html
<!DOCTYPE html><html><body>Coming soon</body></html>
```

- [ ] **Step 3: Smoke test — start the server**

```bash
DATA_DIR=/tmp/jp_test python -m app.main
```

Expected: Server starts on port 13200, no errors. `curl http://localhost:13200/api/lessons` returns `[]`. Stop with Ctrl+C.

- [ ] **Step 4: Commit**

```bash
git add app/main.py frontend/index.html
git commit -m "feat: FastAPI app with startup hooks and static file serving"
```

---

## Task 10: Frontend Shell and CSS

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/css/main.css`
- Create: `frontend/js/app.js`

- [ ] **Step 1: Create `frontend/css/main.css`**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #0f172a;
  --surface: #1e293b;
  --border: #334155;
  --text: #e2e8f0;
  --text-muted: #94a3b8;
  --text-faint: #64748b;
  --accent: #3b82f6;
  --accent-light: #93c5fd;
  --green: #10b981;
  --yellow: #f59e0b;
  --nav-height: 56px;
}

body { background: var(--bg); color: var(--text); font-family: system-ui, sans-serif; min-height: 100vh; }

/* Top navigation */
.top-nav {
  position: fixed; top: 0; left: 0; right: 0; height: var(--nav-height);
  background: var(--surface); border-bottom: 1px solid var(--border);
  display: flex; align-items: center; padding: 0 20px; gap: 24px; z-index: 100;
}
.logo { font-size: 20px; font-weight: bold; color: var(--text); }
.nav-links { display: flex; gap: 20px; }
.nav-link { color: var(--text-muted); text-decoration: none; font-size: 14px; padding-bottom: 2px; }
.nav-link:hover { color: var(--text); }
.nav-link.active { color: var(--accent); border-bottom: 2px solid var(--accent); }
.nav-settings { margin-left: auto; }
.hamburger { display: none; background: none; border: none; color: var(--text); font-size: 20px; cursor: pointer; margin-left: auto; }

/* Mobile menu */
.mobile-menu { display: none; flex-direction: column; background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 20px; gap: 12px; position: fixed; top: var(--nav-height); left: 0; right: 0; z-index: 99; }
.mobile-menu.open { display: flex; }

/* Main content area */
#app { margin-top: var(--nav-height); padding: 24px 20px; max-width: 800px; margin-left: auto; margin-right: auto; }

/* Cards and surfaces */
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }
.card + .card { margin-top: 12px; }

/* Buttons */
.btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; text-decoration: none; }
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: #2563eb; }
.btn-secondary { background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); }
.btn-secondary:hover { color: var(--text); }
.btn-lg { padding: 14px 28px; font-size: 16px; }

/* Progress bar */
.progress-bar { background: var(--bg); border-radius: 4px; height: 8px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.3s; }

/* Character tiles */
.char-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.char-tile { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 8px 12px; font-size: 22px; color: var(--accent-light); }

/* Phase indicator */
.phase-bar { display: flex; gap: 6px; margin-bottom: 24px; }
.phase-dot { flex: 1; height: 4px; border-radius: 2px; background: var(--border); }
.phase-dot.active { background: var(--accent); }
.phase-dot.done { background: var(--green); }

/* Canvas */
.writing-canvas { border: 1px solid var(--border); border-radius: 8px; background: var(--surface); cursor: crosshair; touch-action: none; }

/* Quiz options */
.quiz-options { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.quiz-opt { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; font-size: 24px; text-align: center; cursor: pointer; }
.quiz-opt:hover { border-color: var(--accent); }
.quiz-opt.correct { border-color: var(--green); background: #064e3b; }
.quiz-opt.wrong { border-color: #ef4444; background: #450a0a; }

/* Flashcard */
.flashcard { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 48px 24px; text-align: center; cursor: pointer; min-height: 200px; display: flex; align-items: center; justify-content: center; }
.flashcard-char { font-size: 72px; color: var(--accent-light); }
.flashcard-back { font-size: 24px; color: var(--text); }

/* Recall rating buttons */
.recall-btns { display: flex; gap: 8px; margin-top: 16px; justify-content: center; }
.recall-btn { padding: 10px 20px; border-radius: 8px; border: none; cursor: pointer; font-size: 14px; font-weight: 500; }
.recall-1 { background: #450a0a; color: #fca5a5; }
.recall-2 { background: #431407; color: #fdba74; }
.recall-3 { background: #052e16; color: #86efac; }
.recall-4 { background: #172554; color: #93c5fd; }

/* Labels / headings */
.label { font-size: 11px; letter-spacing: 1px; text-transform: uppercase; color: var(--text-faint); margin-bottom: 8px; }
h2 { font-size: 22px; margin-bottom: 8px; }
h3 { font-size: 16px; margin-bottom: 6px; }
.muted { color: var(--text-muted); font-size: 14px; }

/* Mic button */
.mic-btn { width: 72px; height: 72px; border-radius: 50%; border: 2px solid var(--accent); background: var(--surface); color: var(--accent); font-size: 28px; cursor: pointer; display: flex; align-items: center; justify-content: center; margin: 0 auto; }
.mic-btn.recording { background: #450a0a; border-color: #ef4444; color: #ef4444; animation: pulse 1s infinite; }
@keyframes pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }

/* Responsive */
@media (max-width: 640px) {
  .nav-links, .nav-settings { display: none; }
  .hamburger { display: block; }
  .quiz-options { grid-template-columns: 1fr 1fr; }
  #app { padding: 16px 12px; }
}
```

- [ ] **Step 2: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>日本語</title>
  <link rel="stylesheet" href="/static/css/main.css">
</head>
<body>
  <nav class="top-nav">
    <span class="logo">日本語</span>
    <div class="nav-links">
      <a href="#home" class="nav-link" data-page="home">Home</a>
      <a href="#lessons" class="nav-link" data-page="lessons">Lessons</a>
      <a href="#review" class="nav-link" data-page="review">Review</a>
      <a href="#speak" class="nav-link" data-page="speak">Speak</a>
    </div>
    <button class="hamburger" id="hamburger">☰</button>
    <a href="#home" class="nav-link nav-settings" data-page="home">⚙️</a>
  </nav>
  <div class="mobile-menu" id="mobile-menu">
    <a href="#home" class="nav-link" data-page="home">Home</a>
    <a href="#lessons" class="nav-link" data-page="lessons">Lessons</a>
    <a href="#review" class="nav-link" data-page="review">Review</a>
    <a href="#speak" class="nav-link" data-page="speak">Speak</a>
  </div>
  <main id="app"></main>
  <script src="/static/js/audio.js"></script>
  <script src="/static/js/dashboard.js"></script>
  <script src="/static/js/lesson.js"></script>
  <script src="/static/js/review.js"></script>
  <script src="/static/js/speak.js"></script>
  <script src="/static/js/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Create `frontend/js/app.js`**

```javascript
const pages = { home: renderDashboard, lessons: renderLessons, review: renderReview, speak: renderSpeak };

async function renderLessons() {
  const app = document.getElementById('app');
  const lessons = await fetch('/api/lessons').then(r => r.json());

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
            <button onclick="startLesson(${l.unit},${l.lesson})" class="btn ${l.completed ? 'btn-secondary' : 'btn-primary'}">
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

function navigate(hash) {
  const [page, ...params] = (hash.replace('#', '') || 'home').split('/');
  document.querySelectorAll('.nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  const fn = pages[page];
  if (fn) fn(...params);
}

document.getElementById('hamburger').addEventListener('click', () => {
  document.getElementById('mobile-menu').classList.toggle('open');
});

document.querySelectorAll('.nav-link[data-page]').forEach(a => {
  a.addEventListener('click', () => {
    document.getElementById('mobile-menu').classList.remove('open');
  });
});

window.addEventListener('hashchange', () => navigate(window.location.hash));
navigate(window.location.hash);
```

- [ ] **Step 4: Verify shell loads**

Start the server and open `http://localhost:13200`. Confirm the nav renders, hamburger works on narrow viewport, and hash navigation doesn't error.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: frontend shell with top nav, CSS, and hash router"
```

---

## Task 11: Dashboard Page

**Files:**
- Create: `frontend/js/dashboard.js`

- [ ] **Step 1: Create `frontend/js/dashboard.js`**

```javascript
async function renderDashboard() {
  const app = document.getElementById('app');
  const [lessons, due] = await Promise.all([
    fetch('/api/lessons').then(r => r.json()),
    fetch('/api/review/due').then(r => r.json())
  ]);

  const completed = lessons.filter(l => l.completed);
  const next = lessons.find(l => !l.completed);
  const totalCards = completed.length * 5; // approximate

  // Streak: stored in localStorage
  const today = new Date().toDateString();
  let streak = parseInt(localStorage.getItem('streak') || '0');
  const lastVisit = localStorage.getItem('lastVisit');
  if (lastVisit !== today) {
    const yesterday = new Date(Date.now() - 86400000).toDateString();
    streak = lastVisit === yesterday ? streak + 1 : 1;
    localStorage.setItem('streak', streak);
    localStorage.setItem('lastVisit', today);
  }

  // Group by unit for progress bars
  const unitMap = {};
  for (const l of lessons) {
    if (!unitMap[l.unit]) unitMap[l.unit] = { total: 0, done: 0 };
    unitMap[l.unit].total++;
    if (l.completed) unitMap[l.unit].done++;
  }

  const recentChars = completed.slice(-10).map(l => `<span class="char-tile">?</span>`).join('');

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
            <div class="progress-fill" style="width:${total ? (done/total*100) : 0}%"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
```

- [ ] **Step 2: Verify in browser**

Open `http://localhost:13200`. Dashboard should show streak, continue button (or completion message), review count, and progress bars. With no lessons completed, continue button points to Lesson 1.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/dashboard.js
git commit -m "feat: dashboard with streak, next lesson CTA, and progress bars"
```

---

## Task 12: Audio Utilities

**Files:**
- Create: `frontend/js/audio.js`

- [ ] **Step 1: Create `frontend/js/audio.js`**

```javascript
// TTS: play a Japanese string via the backend
async function playTTS(text) {
  const url = `/api/speech/tts?text=${encodeURIComponent(text)}`;
  const audio = new Audio(url);
  return new Promise((resolve, reject) => {
    audio.onended = resolve;
    audio.onerror = reject;
    audio.play().catch(reject);
  });
}

// Mic recording: returns a Promise<Blob>
function recordAudio(durationMs = 3000) {
  return new Promise((resolve, reject) => {
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      const recorder = new MediaRecorder(stream);
      const chunks = [];
      recorder.ondataavailable = e => chunks.push(e.data);
      recorder.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        resolve(new Blob(chunks, { type: recorder.mimeType }));
      };
      recorder.start();
      setTimeout(() => recorder.stop(), durationMs);
    }).catch(reject);
  });
}

// Send recorded audio to STT endpoint
async function recognizeSpeech(blob, expected = '') {
  const form = new FormData();
  form.append('audio', blob, 'audio.webm');
  const res = await fetch(`/api/speech/recognize?expected=${encodeURIComponent(expected)}`, {
    method: 'POST', body: form
  });
  return res.json(); // { text, expected, match }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/js/audio.js
git commit -m "feat: audio utilities for TTS playback and mic recording"
```

---

## Task 13: Lesson Flow

**Files:**
- Create: `frontend/js/lesson.js`

- [ ] **Step 1: Create `frontend/js/lesson.js`**

```javascript
let lessonData = null;
let currentPhase = 0; // 0=introduce, 1=speak, 2=write, 3=quiz
let currentCardIdx = 0;
let quizResults = [];

async function renderLesson(unit, lesson) {
  if (!unit || !lesson) { window.location.hash = '#lessons'; return; }
  lessonData = await fetch(`/api/lessons/${unit}/${lesson}`).then(r => r.json());
  currentPhase = 0; currentCardIdx = 0; quizResults = [];
  showPhase();
}

function phaseBar() {
  return `<div class="phase-bar">
    ${['Introduce','Speak','Write','Quiz'].map((p, i) => `
      <div class="phase-dot ${i < currentPhase ? 'done' : i === currentPhase ? 'active' : ''}"></div>
    `).join('')}
  </div>`;
}

function showPhase() {
  if (currentPhase === 0) showIntroduce();
  else if (currentPhase === 1) showSpeak();
  else if (currentPhase === 2) showWrite();
  else showQuiz();
}

function showIntroduce() {
  const card = lessonData.cards[currentCardIdx];
  document.getElementById('app').innerHTML = `
    ${phaseBar()}
    <div class="card" style="text-align:center;padding:32px">
      <div style="font-size:80px;color:var(--accent-light)">${card.character}</div>
      <div style="font-size:24px;margin-top:8px">${card.romaji}</div>
      <div class="muted" style="margin-top:4px">${card.meaning}</div>
      <button class="btn btn-secondary" style="margin-top:20px" onclick="playTTS('${card.character}')">🔊 Hear it</button>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px">
      <span class="muted">${currentCardIdx + 1} / ${lessonData.cards.length}</span>
      <button class="btn btn-primary" onclick="nextIntroduce()">Next →</button>
    </div>
  `;
  playTTS(card.character);
}

window.nextIntroduce = function() {
  currentCardIdx++;
  if (currentCardIdx < lessonData.cards.length) showIntroduce();
  else { currentPhase = 1; currentCardIdx = 0; showSpeak(); }
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
  // Pick 5 random quiz questions (or all if fewer)
  const questions = [...cards].sort(() => Math.random() - 0.5).slice(0, Math.min(5, cards.length));
  let qIdx = 0;

  function showQuestion() {
    if (qIdx >= questions.length) { showQuizResults(); return; }
    const q = questions[qIdx];
    // 4 options: 1 correct + 3 distractors from other cards
    const distractors = cards.filter(c => c.id !== q.id).sort(() => Math.random() - 0.5).slice(0, 3);
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
      document.querySelectorAll('.quiz-opt').forEach(o => { if (o.textContent.trim() === correct) o.classList.add('correct'); });
      quizResults.push(false);
    }
    setTimeout(() => { qIdx++; showQuestion(); }, 900);
  };

  showQuestion();
}

async function showQuizResults() {
  const correct = quizResults.filter(Boolean).length;
  const score = `${correct}/${quizResults.length}`;
  await fetch(`/api/lessons/${lessonData.unit}/${lessonData.lesson}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quiz_score: score })
  });
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

// Register the lesson route in app.js page map
if (typeof pages !== 'undefined') pages.lesson = renderLesson;
```

- [ ] **Step 2: Verify in browser**

Start a lesson from the Lessons page. Walk through all 4 phases. Confirm: audio plays on introduce, mic prompt appears on speak, canvas draws on write, quiz shows 4 options with correct/wrong feedback, and lesson completion POSTs to the API.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/lesson.js
git commit -m "feat: 4-phase lesson flow (introduce, speak, write, quiz)"
```

---

## Task 14: Review Session

**Files:**
- Create: `frontend/js/review.js`

- [ ] **Step 1: Create `frontend/js/review.js`**

```javascript
async function renderReview() {
  const app = document.getElementById('app');
  const cards = await fetch('/api/review/due').then(r => r.json());

  if (cards.length === 0) {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:48px">
        <div style="font-size:48px">✅</div>
        <h2 style="margin-top:12px">All caught up!</h2>
        <p class="muted" style="margin-top:8px">No cards due for review.</p>
        <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Back to Home</button>
      </div>
    `;
    return;
  }

  let idx = 0;
  let flipped = false;

  function showCard() {
    if (idx >= cards.length) { showSummary(); return; }
    const card = cards[idx];
    flipped = false;
    app.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h2>Review</h2>
        <span class="muted">${idx + 1} / ${cards.length}</span>
      </div>
      <div class="flashcard" onclick="flipCard('${card.character}','${card.romaji}','${card.meaning}')">
        <div class="flashcard-char">${card.character}</div>
      </div>
      <p class="muted" style="text-align:center;margin-top:12px">Tap card to reveal</p>
      <button class="btn btn-secondary" style="display:block;margin:12px auto" onclick="playTTS('${card.character}')">🔊 Hear it</button>
      <div id="recall-area"></div>
    `;
  }

  window.flipCard = function(char, romaji, meaning) {
    if (flipped) return;
    flipped = true;
    document.querySelector('.flashcard').innerHTML = `
      <div style="text-align:center">
        <div class="flashcard-char" style="font-size:48px">${char}</div>
        <div class="flashcard-back" style="margin-top:8px">${romaji}</div>
        <div class="muted" style="margin-top:4px">${meaning}</div>
      </div>
    `;
    document.getElementById('recall-area').innerHTML = `
      <p class="muted" style="text-align:center;margin-top:16px;margin-bottom:8px">How well did you remember?</p>
      <div class="recall-btns">
        <button class="recall-btn recall-1" onclick="rate(1)">Forgot</button>
        <button class="recall-btn recall-2" onclick="rate(2)">Hard</button>
        <button class="recall-btn recall-3" onclick="rate(3)">Good</button>
        <button class="recall-btn recall-4" onclick="rate(4)">Easy</button>
      </div>
    `;
  };

  window.rate = async function(score) {
    const card = cards[idx];
    await fetch('/api/review/update', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: card.id, score })
    });
    idx++;
    showCard();
  };

  function showSummary() {
    app.innerHTML = `
      <div class="card" style="text-align:center;padding:40px">
        <div style="font-size:48px">🎴</div>
        <h2 style="margin-top:12px">Review Complete</h2>
        <p class="muted" style="margin-top:8px">${cards.length} cards reviewed</p>
        <button class="btn btn-primary" style="margin-top:20px" onclick="window.location.hash='#home'">Back to Home</button>
      </div>
    `;
  }

  showCard();
}
```

- [ ] **Step 2: Verify in browser**

Complete a lesson first so cards enter the review queue. Go to Review page. Confirm: card shows character, tap reveals reading + meaning, recall buttons appear, rating POSTs to API, counter advances, summary shows at end.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/review.js
git commit -m "feat: SRS flashcard review session with recall rating"
```

---

## Task 15: Speaking Practice Page

**Files:**
- Create: `frontend/js/speak.js`

- [ ] **Step 1: Create `frontend/js/speak.js`**

```javascript
async function renderSpeak() {
  const app = document.getElementById('app');
  const lessons = await fetch('/api/lessons').then(r => r.json());
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

  // Load all cards from completed lessons
  const allCards = [];
  for (const l of completed) {
    const data = await fetch(`/api/lessons/${l.unit}/${l.lesson}`).then(r => r.json());
    allCards.push(...data.cards);
  }

  let current = null;

  function pickRandom() {
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
  }

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

- [ ] **Step 2: Verify in browser**

Complete a lesson, then visit Speak page. Confirm: random card appears, TTS plays, mic records and shows Whisper result, Next picks a different card.

- [ ] **Step 3: Commit**

```bash
git add frontend/js/speak.js
git commit -m "feat: freeform speaking practice page"
```

---

## Task 16: Docker Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `Dockerfile`**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

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

- [ ] **Step 2: Create `docker-compose.yml`**

```yaml
services:
  app:
    build: .
    ports:
      - "13200:13200"
    volumes:
      - /mnt/secdrive/docker/data/japanese-learning:/data
      - /mnt/secdrive/docker/config/japanese-learning:/config
    restart: unless-stopped
    environment:
      - DATA_DIR=/data
      - CONFIG_DIR=/config
      - PORT=13200
```

- [ ] **Step 3: Create host directories on Linux server**

```bash
mkdir -p /mnt/secdrive/docker/data/japanese-learning
mkdir -p /mnt/secdrive/docker/config/japanese-learning
```

- [ ] **Step 4: Build and start**

```bash
docker compose build
docker compose up -d
docker compose logs -f
```

Expected: Server starts, seed runs, no errors in logs.

- [ ] **Step 5: Verify from browser**

Open `http://<server-ip>:13200` (or your Caddy HTTPS URL). Confirm app loads. Navigate all pages. Start Lesson 1.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: Docker deployment with bind mounts on port 13200"
```

---

## Task 17: Unit 2 Katakana Content

**Files:**
- Create: `lessons/unit2/lesson01.json` through `lesson20.json`

Katakana mirrors hiragana exactly in structure. All files use `"type": "katakana"` and `"unit": 2`.

- [ ] **Step 1: Create lessons 01–03**

`lesson01.json`:
```json
{
  "unit": 2, "lesson": 1, "title": "Katakana — Vowels (ア行)",
  "cards": [
    {"type": "katakana", "character": "ア", "romaji": "a", "meaning": "vowel 'a'"},
    {"type": "katakana", "character": "イ", "romaji": "i", "meaning": "vowel 'i'"},
    {"type": "katakana", "character": "ウ", "romaji": "u", "meaning": "vowel 'u'"},
    {"type": "katakana", "character": "エ", "romaji": "e", "meaning": "vowel 'e'"},
    {"type": "katakana", "character": "オ", "romaji": "o", "meaning": "vowel 'o'"}
  ]
}
```

`lesson02.json`:
```json
{
  "unit": 2, "lesson": 2, "title": "Katakana — K-row (カ行)",
  "cards": [
    {"type": "katakana", "character": "カ", "romaji": "ka", "meaning": "ka"},
    {"type": "katakana", "character": "キ", "romaji": "ki", "meaning": "ki"},
    {"type": "katakana", "character": "ク", "romaji": "ku", "meaning": "ku"},
    {"type": "katakana", "character": "ケ", "romaji": "ke", "meaning": "ke"},
    {"type": "katakana", "character": "コ", "romaji": "ko", "meaning": "ko"}
  ]
}
```

`lesson03.json`:
```json
{
  "unit": 2, "lesson": 3, "title": "Katakana — S-row (サ行)",
  "cards": [
    {"type": "katakana", "character": "サ", "romaji": "sa", "meaning": "sa"},
    {"type": "katakana", "character": "シ", "romaji": "shi", "meaning": "shi"},
    {"type": "katakana", "character": "ス", "romaji": "su", "meaning": "su"},
    {"type": "katakana", "character": "セ", "romaji": "se", "meaning": "se"},
    {"type": "katakana", "character": "ソ", "romaji": "so", "meaning": "so"}
  ]
}
```

- [ ] **Step 2: Create lessons 04–20**

Use the same structure. Content:

| File | Title | Characters |
|---|---|---|
| `lesson04.json` | T-row (タ行) | タ=ta, チ=chi, ツ=tsu, テ=te, ト=to |
| `lesson05.json` | N-row (ナ行) | ナ=na, ニ=ni, ヌ=nu, ネ=ne, ノ=no |
| `lesson06.json` | H-row (ハ行) | ハ=ha, ヒ=hi, フ=fu, ヘ=he, ホ=ho |
| `lesson07.json` | M-row (マ行) | マ=ma, ミ=mi, ム=mu, メ=me, モ=mo |
| `lesson08.json` | Y-row (ヤ行) | ヤ=ya, ユ=yu, ヨ=yo |
| `lesson09.json` | R-row (ラ行) | ラ=ra, リ=ri, ル=ru, レ=re, ロ=ro |
| `lesson10.json` | W-row + N (ワ行) | ワ=wa, ヲ=wo, ン=n |
| `lesson11.json` | G-row (ガ行) | ガ=ga, ギ=gi, グ=gu, ゲ=ge, ゴ=go |
| `lesson12.json` | Z-row (ザ行) | ザ=za, ジ=ji, ズ=zu, ゼ=ze, ゾ=zo |
| `lesson13.json` | D-row (ダ行) | ダ=da, ヂ=ji (rare), ヅ=zu (rare), デ=de, ド=do |
| `lesson14.json` | B-row (バ行) | バ=ba, ビ=bi, ブ=bu, ベ=be, ボ=bo |
| `lesson15.json` | P-row (パ行) | パ=pa, ピ=pi, プ=pu, ペ=pe, ポ=po |
| `lesson16.json` | KI+SHI combos | キャ=kya, キュ=kyu, キョ=kyo, シャ=sha, シュ=shu, ショ=sho |
| `lesson17.json` | CHI+NI combos | チャ=cha, チュ=chu, チョ=cho, ニャ=nya, ニュ=nyu, ニョ=nyo |
| `lesson18.json` | HI+MI combos | ヒャ=hya, ヒュ=hyu, ヒョ=hyo, ミャ=mya, ミュ=myu, ミョ=myo |
| `lesson19.json` | RI combos | リャ=rya, リュ=ryu, リョ=ryo |
| `lesson20.json` | Voiced combos | ギャ=gya, ギュ=gyu, ギョ=gyo, ジャ=ja, ジュ=ju, ジョ=jo, ビャ=bya, ビュ=byu, ビョ=byo, ピャ=pya, ピュ=pyu, ピョ=pyo |

- [ ] **Step 3: Rebuild Docker image to include new lessons**

```bash
docker compose build && docker compose up -d
```

- [ ] **Step 4: Commit**

```bash
git add lessons/unit2/
git commit -m "feat: Unit 2 katakana lesson content (20 lessons)"
```

---

## Self-Review Notes

**Spec coverage check:**
- ✅ Architecture: FastAPI + aiosqlite + Whisper + edge-tts + Docker
- ✅ Deployment: Bind mounts at `/mnt/secdrive/docker/data|config/japanese-learning`, port 13200
- ✅ Curriculum: Hiragana (20 lessons) + Katakana (20 lessons); Unit 3–5 added via JSON files
- ✅ Lesson flow: 4 phases (Introduce, Speak, Write, Quiz)
- ✅ SRS: SM-2 algorithm, due cards, recall rating
- ✅ TTS: edge-tts with Nanami voice, MP3 cache
- ✅ STT: local Whisper base, 10s timeout, graceful fallback
- ✅ UI: Top nav, responsive, hamburger on mobile, dark theme
- ✅ Dashboard: streak, CTA, progress bars
- ✅ Review session: flashcard flip, recall rating, summary
- ✅ Speaking practice: freeform, random card from completed lessons
- ✅ Writing: canvas with touch support, hint overlay
- ✅ Error handling: mic unavailable, Whisper timeout, edge-tts fallback
- ✅ Single user, no auth
- ✅ Lesson JSON editable without code changes

**Unit 3–5 content:** Not included in this plan — add by creating `lessons/unit3/`, `lessons/unit4/`, `lessons/unit5/` JSON files following the same schema. No code changes required.
