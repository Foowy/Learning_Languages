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
