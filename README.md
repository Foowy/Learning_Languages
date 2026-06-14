# Learning_Languages

A personal language learning web app for complete beginners. Supports Japanese, Korean, Mandarin, and ASL with spaced repetition, TTS pronunciation, and speech recognition.

## Features

- **Spaced repetition** (SM-2) for vocabulary review
- **TTS pronunciation** via Microsoft Edge neural voices
- **Speech recognition** via OpenAI Whisper
- **Multi-user** profile support
- **Multi-language**: Japanese (hiragana → katakana → kanji → vocab), Korean, Mandarin (HSK 1–6), ASL
- **Lesson packs** downloaded at runtime — no content baked into the image

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, uvicorn |
| Frontend | Vanilla HTML/CSS/JS |
| Database | SQLite via aiosqlite |
| TTS | edge-tts (Microsoft Edge neural voices) |
| STT | openai-whisper |
| Container | Docker + Docker Compose |

## Running

```bash
docker compose up -d
# App runs on port 13200
```

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `DATA_DIR` | `/data` | SQLite DB, audio cache, lessons, Whisper model |
| `CONFIG_DIR` | `/config` | App config overrides |
| `PORT` | `13200` | Server port |
| `LESSONS_PACK_URL` | — | `.tar.gz` URL downloaded on first start or version change |
| `LESSONS_PACK_VERSION` | — | Bump to force re-download (e.g. a date string) |
| `WHISPER_MODEL` | `base` | Model size: `tiny`/`base`/`small`/`medium`/`large` |
| `WHISPER_PRELOAD` | `false` | Load Whisper at startup to eliminate first-request latency |

## Lesson Packs

Lesson content is not bundled in the image. On first start the app downloads a pack from `LESSONS_PACK_URL` and extracts it to `DATA_DIR/lessons/`.

To regenerate the pack from upstream sources, trigger the **Update Lesson Packs** GitHub Actions workflow. It downloads the latest jmdict-simplified, HSK, and ASL data, runs the converters, and publishes a new `lessons-latest` release asset automatically.

To manually build a pack:

```bash
# Japanese kanji (units 3–6) — requires kanjidic2-en-*.json from jmdict-simplified releases
python tools/convert_kanjidic.py --input kanjidic2-en-<version>.json

# Japanese vocabulary (unit 7+) — requires jmdict-eng-common-*.json from jmdict-simplified releases
python tools/convert_jmdict.py --input jmdict-eng-common-<version>.json

# Mandarin HSK 1–6 — requires hsk-level-{1..6}.json from clem109/hsk-vocabulary
python tools/convert_hsk.py --input /path/to/hsk-files/

# ASL — no download needed
python tools/gen_asl_lessons.py

# Package
cd lessons/ && tar -czf ../lessons.tar.gz .
```

## Attributions

| Content | Source | Licence |
|---|---|---|
| JMdict / KanjiDic2 | [jmdict-simplified](https://github.com/scriptin/jmdict-simplified) | CC BY-SA 4.0 (EDRDG) |
| HSK vocabulary | [clem109/hsk-vocabulary](https://github.com/clem109/hsk-vocabulary) | CC BY 4.0 |
| TTS voices | Microsoft Edge Read Aloud via [edge-tts](https://github.com/rany2/edge-tts) | MIT |
| Speech recognition | [openai-whisper](https://github.com/openai/whisper) | MIT |

Distributed lesson packs derived from JMdict or KanjiDic2 must carry a CC BY-SA 4.0 notice crediting the [Electronic Dictionary Research and Development Group](https://www.edrdg.org/edrdg/licence.html).
