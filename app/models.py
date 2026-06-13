from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class UserCreate(BaseModel):
    name: str

class ReviewUpdate(BaseModel):
    card_id: int
    score: int = Field(ge=1, le=4)  # SM-2 scale: 1=blackout, 2=hard, 3=good, 4=easy

class LessonComplete(BaseModel):
    quiz_score: str  # e.g. "4/5"

class TranscriptionResult(BaseModel):
    text: str
    expected: str
    match: bool
