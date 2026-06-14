# STT powered by openai-whisper (MIT) — https://github.com/openai/whisper
# Model is downloaded on first use and cached in DATA_DIR/models/whisper/.
import asyncio
import tempfile
from pathlib import Path

from app.config import settings

_model = None

_LANGUAGES = {
    "japanese": "ja",
    "korean": "ko",
    "mandarin": "zh",
    "chinese": "zh",
}

def get_model():
    global _model
    if _model is None:
        import whisper
        model_dir = Path(settings.data_dir) / "models" / "whisper"
        model_dir.mkdir(parents=True, exist_ok=True)
        _model = whisper.load_model(settings.whisper_model, download_root=str(model_dir))
    return _model

async def transcribe(audio_bytes: bytes, suffix: str = ".webm", language: str = "japanese") -> str:
    model = get_model()
    whisper_lang = _LANGUAGES.get(language, language)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name
    result = await asyncio.to_thread(
        model.transcribe, tmp_path, language=whisper_lang, fp16=False
    )
    Path(tmp_path).unlink(missing_ok=True)
    return result["text"].strip()
