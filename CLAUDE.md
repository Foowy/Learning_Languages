# Learning Languages — Claude Code Guide

## Project Overview

A personal language learning web app for complete beginners. Currently focused on Japanese (hiragana → katakana → kanji → vocabulary), with multi-language and multi-user support in progress. Runs as a Docker container on a home Linux server behind a Caddy HTTPS proxy.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI 0.111.0, uvicorn |
| Frontend | Vanilla HTML/CSS/JS — no build step |
| Database | SQLite via `aiosqlite` |
| TTS | `edge-tts` (Microsoft neural, Nanami JP voice) |
| STT | `openai-whisper` (base model, CPU only) |
| Container | Docker + Docker Compose |
| HTTPS | Caddy (user-managed, external) |

## Project Structure

```
app/
  config.py         — pydantic-settings (data_dir, config_dir, port)
  database.py       — DDL constants (CREATE_USERS/CARDS/PROGRESS/LESSONS), init_db(), get_db()
  models.py         — Pydantic request models
  seed.py           — Seeds cards from lessons/ JSON on first run
  main.py           — FastAPI app, router registration, static mounts
  routers/
    users.py        — GET/POST /api/users, POST /api/users/{id}/avatar
    languages.py    — GET /api/languages (stub → full in Task 5)
    lessons.py      — GET /api/lessons, GET /api/lessons/{unit}/{lesson}, POST complete
    progress.py     — GET /api/review/due, POST /api/review/update
    speech.py       — POST /api/speech/tts, POST /api/speech/recognize
  services/
    srs.py          — SM-2 spaced repetition algorithm
    tts.py          — edge-tts wrapper with file cache
    stt.py          — Whisper wrapper
frontend/
  index.html        — App shell, nav, script tags
  css/main.css
  js/
    audio.js        — TTS playback + mic recording helpers
    app.js          — Router, page registry, nav handlers
    dashboard.js    — Home page
    lesson.js       — 4-phase lesson flow (introduce/speak/write/quiz)
    review.js       — SRS flashcard session
    speak.js        — Freeform speaking practice
lessons/
  japanese/
    unit1/          — 20 hiragana JSON lessons
    unit2/          — 20 katakana JSON lessons
tests/
  conftest.py       — test_db + client fixtures (creates "Tester" user id=1)
  test_database.py
  test_lessons.py
  test_progress.py
  test_seed.py      — NOTE: excluded during multi-user Tasks 1–5 (path changed, fixed in Task 6)
  test_speech.py / test_tts.py / test_stt.py
  test_srs.py
  test_users.py
```

## Running Tests

```bash
# Full suite (test_seed.py is broken until Task 6 is done)
pytest tests/ -v --ignore=tests/test_seed.py

# After Task 6, run everything
pytest tests/ -v
```

`asyncio_mode = auto` is set in `pytest.ini` — no need to add `@pytest.mark.asyncio` decorators.

## Configuration

Settings come from environment variables or `.env` file (see `.env.example`):

- `DATA_DIR` — where SQLite DB, audio cache, and lesson JSON live (default: `/data`)
- `CONFIG_DIR` — app config overrides (default: `/config`)
- `PORT` — server port (default: `13200`)

In tests, monkeypatch `app.database.get_db_path` or `app.config.settings.data_dir` to redirect to `tmp_path`.

## Database

SQLite at `{DATA_DIR}/progress.db`. Key tables:

- `users` — id, name, avatar_path, created_at
- `cards` — id, type, character, romaji, meaning, unit, lesson, language, audio_path
- `progress` — PK (card_id, user_id), SRS fields (due_date, interval_days, ease_factor, review_count, last_score)
- `lessons` — PK (lesson_id, unit, language, user_id), completed_at, quiz_score

`init_db()` in `database.py` handles both fresh installs and in-place migration from the old single-user schema.

## Lesson Content

Lesson JSON files live at `lessons/{language}/unit{N}/lesson{N}.json`. The seed reads the language name from the folder path (first segment after `lessons/`). Format:

```json
{
  "unit": 1,
  "lesson": 1,
  "title": "Hiragana Row 1",
  "cards": [
    { "type": "hiragana", "character": "あ", "romaji": "a", "meaning": "vowel a" }
  ]
}
```

## Docker

```bash
# Build and run locally
docker compose up -d

# App runs on port 13200
# Caddy on the server terminates HTTPS and proxies to http://app:13200
```

Host bind mounts:
- `/mnt/secdrive/docker/data/japanese-learning/` → `/data`
- `/mnt/secdrive/docker/config/japanese-learning/` → `/config`

## In-Progress: Multi-User + Multi-Language

**Plan:** [docs/superpowers/plans/2026-06-13-multi-user-multilanguage.md](docs/superpowers/plans/2026-06-13-multi-user-multilanguage.md)

13 tasks total. Current status (as of 2026-06-13):

| Task | Description | Status |
|---|---|---|
| 1 | Move lessons to `lessons/japanese/` | ✅ Done |
| 2 | DB schema: users table + migration | ✅ Done |
| 3 | Pillow dependency | ✅ Done |
| 4 | Users API (list/create/avatar) | ✅ Done |
| 5 | Languages API (auto-discover folders) | ✅ Done |
| 6 | Seed update (language from path) | ✅ Done |
| 7 | Lessons router: user_id + language params | ✅ Done |
| 8 | Progress router: user_id + language params | ✅ Done |
| 9 | Frontend index.html + nav buttons | ✅ Done |
| 10 | Frontend users.js (profile picker) | ✅ Done |
| 11 | Frontend languages.js (language picker) | ✅ Done |
| 12 | Frontend app.js (session helpers, gating) | ✅ Done |
| 13 | Frontend page updates (apiParams + ASL) | ✅ Done |

**Status:** All 13 tasks complete as of 2026-06-14. Implementation is feature-complete.

## Known Deprecation Warnings (Pre-existing, Not Blockers)

- `@app.on_event("startup")` — deprecated in newer FastAPI; will need migration to `lifespan`
- `datetime.utcnow()` — deprecated in Python 3.12+; use `datetime.now(UTC)` eventually
