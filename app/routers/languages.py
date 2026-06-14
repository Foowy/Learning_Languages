from pathlib import Path
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/languages", tags=["languages"])

LANGUAGE_LABELS = {
    "japanese": "🇯🇵 Japanese",
    "spanish": "🇪🇸 Spanish (Latin America)",
    "asl": "🤟 ASL",
}

@router.get("")
async def list_languages():
    lessons_dir = Path(settings.data_dir) / "lessons"
    if not lessons_dir.exists():
        return []
    result = []
    for lang_dir in sorted(lessons_dir.iterdir()):
        if not lang_dir.is_dir():
            continue
        lesson_count = sum(1 for _ in lang_dir.rglob("lesson*.json"))
        label = LANGUAGE_LABELS.get(lang_dir.name, lang_dir.name.capitalize())
        result.append({
            "language": lang_dir.name,
            "label": label,
            "lesson_count": lesson_count,
        })
    return result
