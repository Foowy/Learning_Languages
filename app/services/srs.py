from dataclasses import dataclass
from datetime import date, timedelta

@dataclass
class SRSCard:
    interval_days: int
    ease_factor: float
    review_count: int

def next_interval(card: SRSCard, score: int) -> SRSCard:
    """SM-2 algorithm. score: 1=blackout, 2=hard, 3=good, 4=easy."""
    new_ease = max(1.3, card.ease_factor + (0.1 - (4 - score) * (0.08 + (4 - score) * 0.02)))

    if score < 2:
        return SRSCard(interval_days=1, ease_factor=card.ease_factor, review_count=card.review_count + 1)

    if card.review_count == 0:
        new_interval = 1
    elif card.review_count == 1:
        new_interval = 6
    else:
        new_interval = round(card.interval_days * new_ease)

    return SRSCard(interval_days=new_interval, ease_factor=new_ease, review_count=card.review_count + 1)

def due_date(interval_days: int) -> date:
    return date.today() + timedelta(days=interval_days)
