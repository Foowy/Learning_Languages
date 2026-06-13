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
