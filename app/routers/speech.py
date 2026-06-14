import asyncio
from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import FileResponse
from app.services.tts import get_audio
from app.services.stt import transcribe

router = APIRouter(prefix="/api/speech", tags=["speech"])

@router.get("/tts")
async def text_to_speech(
    text: str = Query(...),
    language: str = Query(default="japanese"),
):
    path = await get_audio(text, language)
    return FileResponse(str(path), media_type="audio/mpeg")

@router.post("/recognize")
async def speech_to_text(
    audio: UploadFile = File(...),
    expected: str = Query(default=""),
    language: str = Query(default="japanese"),
):
    audio_bytes = await audio.read()
    suffix = ".webm" if "webm" in (audio.content_type or "") else ".wav"
    try:
        text = await asyncio.wait_for(transcribe(audio_bytes, suffix, language), timeout=10.0)
    except asyncio.TimeoutError:
        return {"error": "timeout", "text": "", "expected": expected, "match": False}
    return {"text": text, "expected": expected, "match": text == expected}
