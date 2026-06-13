from app.services.srs import SRSCard, next_interval, due_date
from datetime import date, timedelta

def test_score_below_2_resets_interval():
    card = SRSCard(interval_days=10, ease_factor=2.5, review_count=5)
    result = next_interval(card, score=1)
    assert result.interval_days == 1

def test_first_review_gives_interval_1():
    card = SRSCard(interval_days=1, ease_factor=2.5, review_count=0)
    result = next_interval(card, score=3)
    assert result.interval_days == 1
    assert result.review_count == 1

def test_second_review_gives_interval_6():
    card = SRSCard(interval_days=1, ease_factor=2.5, review_count=1)
    result = next_interval(card, score=3)
    assert result.interval_days == 6

def test_subsequent_review_multiplies_by_ease():
    card = SRSCard(interval_days=6, ease_factor=2.5, review_count=2)
    result = next_interval(card, score=3)
    assert result.interval_days == 15  # round(6 * 2.5)

def test_ease_decreases_on_hard():
    card = SRSCard(interval_days=6, ease_factor=2.5, review_count=2)
    result = next_interval(card, score=2)
    assert result.ease_factor < 2.5

def test_ease_never_below_1_3():
    card = SRSCard(interval_days=1, ease_factor=1.3, review_count=3)
    result = next_interval(card, score=1)
    assert result.ease_factor >= 1.3

def test_due_date_is_today_plus_interval():
    d = due_date(3)
    assert d == date.today() + timedelta(days=3)
