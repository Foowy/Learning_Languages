# TTS powered by edge-tts (MIT) — wraps Microsoft Edge Read Aloud neural voices.
# Voice list: https://github.com/rany2/edge-tts
import hashlib
from pathlib import Path
import edge_tts
from app.config import settings

AUDIO_DIR = Path(settings.data_dir) / "audio"

_VOICES = {
    "japanese": "ja-JP-NanamiNeural",
    "korean": "ko-KR-SunHiNeural",
    "mandarin": "zh-CN-XiaoxiaoNeural",
    "chinese": "zh-CN-XiaoxiaoNeural",
}
_DEFAULT_VOICE = "en-US-JennyNeural"

async def get_audio(text: str, language: str = "japanese") -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    voice = _VOICES.get(language, _DEFAULT_VOICE)
    key = hashlib.md5(f"{language}:{text}".encode()).hexdigest()
    path = AUDIO_DIR / f"{key}.mp3"
    if path.exists() and path.stat().st_size == 0:
        path.unlink()
    if not path.exists():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(path))
        if not path.exists() or path.stat().st_size == 0:
            path.unlink(missing_ok=True)
            raise RuntimeError(f"edge-tts returned empty audio for: {text!r}")
    return path
