# Multi-User & Multi-Language Design

**Goal:** Add family user profiles (2–5 users, no auth) and multi-language support (Japanese, Latin American Spanish, ASL) to the existing learning app, with per-user per-language progress tracking.

**Architecture:** Single shared SQLite DB gains `users` table and `user_id` / `language` columns on existing progress tables. Language folders under `lessons/` are auto-discovered. Session state (active user + language) stored in `sessionStorage`. Two new frontend screens (user picker, language picker) gate entry to the app.

**Tech Stack:** Same as existing — FastAPI, aiosqlite, vanilla JS. New: `Pillow` for avatar image resizing.

---

## Lesson File Structure

Lesson JSON files move from `lessons/unit{N}/` to `lessons/{language}/unit{N}/`:

```
lessons/
  japanese/
    unit1/   ← hiragana (existing lesson01–20.json, relocated)
    unit2/   ← katakana (existing lesson01–20.json, relocated)
  spanish/
    unit1/   ← (future content)
  asl/
    unit1/   ← (future content, cards include "video" field)
```

Adding a new language requires only dropping a new folder here — no code changes.

---

## Database Schema Changes

### New table: `users`

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    avatar_path TEXT,
    created_at DATETIME NOT NULL DEFAULT (datetime('now'))
)
```

### Modified table: `cards`

Add column:
```sql
ALTER TABLE cards ADD COLUMN language TEXT NOT NULL DEFAULT 'japanese'
```

Primary key for card uniqueness becomes `(language, unit, lesson, character)` conceptually — `id` remains the surrogate key.

### Modified table: `progress`

Old PK: `card_id`
New PK: `(card_id, user_id)`

```sql
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
```

### Modified table: `lessons`

Old PK: `(lesson_id, unit)`
New PK: `(lesson_id, unit, language, user_id)`

```sql
CREATE TABLE IF NOT EXISTS lessons (
    lesson_id INTEGER NOT NULL,
    unit INTEGER NOT NULL,
    language TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id),
    completed_at DATETIME,
    quiz_score TEXT,
    PRIMARY KEY (lesson_id, unit, language, user_id)
)
```

### Migration

On startup, `init_db()` runs migration logic:
1. Creates `users` table if absent.
2. Adds `language` column to `cards` if absent (default `'japanese'`).
3. Recreates `progress` and `lessons` with new PKs if they lack `user_id` (detected by checking column names via `PRAGMA table_info`). Existing rows are copied into the new tables before the old ones are dropped.
4. If existing progress/lesson rows exist without `user_id`, creates a default user named "Player 1" and assigns all existing rows to them.

---

## Media Storage

All files live under `/data` (host-mounted volume):

```
/data/
  progress.db
  avatars/          ← profile images, served at /avatars/
    1.jpg
    2.jpg
  videos/           ← ASL video clips, served at /videos/
    asl/
      hello.mp4
  tts_cache/        ← existing TTS MP3 cache
```

- Avatar upload: multipart POST, saved as JPEG via Pillow (max 512×512), stored as `/data/avatars/{user_id}.jpg`.
- ASL videos: dropped manually on the server into `/data/videos/asl/`. No upload UI.
- FastAPI gets two new `StaticFiles` mounts: `/avatars` and `/videos`.

---

## API

### New router: `app/routers/users.py`

```
GET  /api/users                   List all profiles [{id, name, avatar_url}]
POST /api/users                   Create profile {name}  → {id, name}
POST /api/users/{id}/avatar       Upload avatar (multipart) → {avatar_url}
```

### New router: `app/routers/languages.py`

```
GET  /api/languages               Scan lessons/ dir → [{language, label, unit_count, lesson_count}]
```

### Modified routes (all gain query params)

```
GET  /api/lessons?user_id=1&language=japanese
GET  /api/lessons/{unit}/{lesson}?language=japanese
POST /api/lessons/{unit}/{lesson}/complete   body gains user_id + language
GET  /api/review/due?user_id=1&language=japanese
POST /api/review/update                      body gains user_id
```

TTS and STT routes are unchanged (language-agnostic).

---

## Frontend

### New files

- `frontend/js/users.js` — profile picker screen + new profile creation form
- `frontend/js/languages.js` — language selection screen

### Modified files

- `frontend/js/app.js` — startup gating, sessionStorage helpers, language switcher in nav
- `frontend/js/dashboard.js`, `lesson.js`, `review.js`, `speak.js` — all fetch calls gain `user_id` and `language` params
- `frontend/index.html` — add `<script>` tags for `users.js` and `languages.js`

### App startup flow

```
App loads
  → sessionStorage has userId?
      No  → render user picker (users.js)
      Yes → sessionStorage has currentLanguage?
              No  → render language picker (languages.js)
              Yes → navigate(window.location.hash || '#home')
```

### User picker screen (`users.js`)

- Fetches `GET /api/users`
- Renders profile cards: avatar image (or CSS initials circle fallback) + name
- Last card is always "+ New Profile"
- New Profile form: name text input + optional avatar file upload
- On profile select: `sessionStorage.setItem('userId', id)`, `sessionStorage.setItem('userName', name)`, then check language

### Language picker screen (`languages.js`)

- Fetches `GET /api/languages`
- Renders language cards: language name + lesson count
- On select: `sessionStorage.setItem('currentLanguage', language)`, navigate to `#home`

### Nav changes

- Language indicator added to top nav (e.g., "🇯🇵 Japanese") 
- Clicking it renders the language picker to allow switching
- "Switch User" link added (clears `sessionStorage`, re-renders user picker)

### sessionStorage helpers (in `app.js`)

```javascript
function getCurrentUser() {
  return { id: sessionStorage.getItem('userId'), name: sessionStorage.getItem('userName') };
}
function getCurrentLanguage() {
  return sessionStorage.getItem('currentLanguage') || 'japanese';
}
function apiParams() {
  return `user_id=${getCurrentUser().id}&language=${getCurrentLanguage()}`;
}
```

All fetch calls become e.g. `fetch('/api/lessons?' + apiParams())`.

### ASL-specific lesson rendering

In `lesson.js`, if `getCurrentLanguage() === 'asl'`:
- Introduce phase: render `<video src="/videos/asl/${card.video}" controls autoplay loop>` instead of character display
- Speak phase: hidden entirely (no mic, no TTS)
- Write phase: unchanged (drawing still applies)
- Quiz phase: unchanged (multiple choice on meaning still works)

Card JSON for ASL adds optional field: `"video": "hello.mp4"`

---

## Language Labels

| Folder name | Display label |
|-------------|---------------|
| `japanese`  | 🇯🇵 Japanese  |
| `spanish`   | 🇪🇸 Spanish (Latin America) |
| `asl`       | 🤟 ASL        |

Labels are derived from a mapping in `app/routers/languages.py`. Unknown folders fall back to their folder name capitalized.

---

## Out of Scope

- Authentication / passwords
- ASL video upload UI (videos dropped manually on server)
- Spanish or ASL lesson content (folder structure ready, content added later)
- Cross-user statistics or leaderboards
- Per-user language progress shown on the user picker screen
