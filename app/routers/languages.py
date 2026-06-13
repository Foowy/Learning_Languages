# app/routers/languages.py (stub — full implementation in Task 5)
from fastapi import APIRouter
router = APIRouter(prefix="/api/languages", tags=["languages"])

@router.get("")
async def list_languages():
    return []
