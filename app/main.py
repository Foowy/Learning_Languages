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
