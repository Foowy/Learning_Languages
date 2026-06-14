import asyncio
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
    if settings.whisper_preload:
        from app.services.stt import get_model
        await asyncio.to_thread(get_model)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=False)
