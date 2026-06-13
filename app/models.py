from pydantic import BaseModel

class ReviewUpdate(BaseModel):
    card_id: int
    score: int  # 1–4

class LessonComplete(BaseModel):
    quiz_score: str  # e.g. "4/5"

class TranscriptionResult(BaseModel):
    text: str
    expected: str
    match: bool
