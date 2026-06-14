#!/usr/bin/env python3
"""
Convert jmdict-simplified JSON into vocabulary lesson packs for learning_languages.

Data source
-----------
Download a jmdict-simplified release from:
  https://github.com/scriptin/jmdict-simplified/releases

  Recommended file: jmdict-english-common.json  (common words only, ~8 MB)
  Full file:        jmdict-english.json          (~50 MB, use --common-only to filter)

Licence: CC BY-SA 4.0 — Electronic Dictionary Research and Development Group
  https://www.edrdg.org/edrdg/licence.html
If you distribute a lessons pack derived from this data, include the above credit.

Frequency sorting
-----------------
Words are sorted by newspaper frequency using the "nf" tags on kanji/kana entries
(nf01 = most frequent ~500 words, nf48 = least frequent of the tagged set).
Words without an nf tag are placed after all ranked words.

Output
------
Words are written in frequency order, split into units of --words-per-unit (default 200)
starting at --start-unit (default 7, after 4 kanjidic units).

  lessons/japanese/unit7/lesson01.json  → words 1–10
  lessons/japanese/unit7/lesson02.json  → words 11–20
  ...
  lessons/japanese/unit8/lesson01.json  → words 201–210
  ...

Card format produced
--------------------
  {
    "type": "kanji",        (or "kana" for kana-only words)
    "character": "食べる",
    "romaji": "たべる",
    "meaning": "to eat"
  }

  character: first kanji form, or first kana form if no kanji exists.
  romaji:    first kana form.
  meaning:   first 2 English glosses from the first sense, joined by "; ".

Usage
-----
  python tools/convert_jmdict.py --input jmdict-english-common.json
  python tools/convert_jmdict.py --input jmdict-english.json --common-only \\
      --start-unit 7 --words-per-unit 200 --cards-per-lesson 10
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path


def _nf_rank(tags: list[str]) -> int:
    """Return the numeric rank from the lowest nf tag (nf01=1 … nf48=48), or 999 if none."""
    ranks = []
    for t in tags:
        m = re.fullmatch(r"nf(\d+)", t)
        if m:
            ranks.append(int(m.group(1)))
    return min(ranks) if ranks else 999


def _word_rank(word: dict) -> int:
    best = 999
    for entry in word.get("kanji", []) + word.get("kana", []):
        best = min(best, _nf_rank(entry.get("tags", [])))
    return best


def _is_common(word: dict) -> bool:
    for entry in word.get("kanji", []) + word.get("kana", []):
        if entry.get("common"):
            return True
    return False


def _card(word: dict) -> dict | None:
    kanji_entries = word.get("kanji", [])
    kana_entries  = word.get("kana", [])

    if not kana_entries:
        return None

    if kanji_entries:
        character = kanji_entries[0]["text"]
        card_type = "kanji"
    else:
        character = kana_entries[0]["text"]
        card_type = "kana"

    romaji = kana_entries[0]["text"]

    glosses = []
    for sense in word.get("sense", []):
        for g in sense.get("gloss", []):
            if g.get("lang") == "eng":
                glosses.append(g["text"])
        if glosses:
            break  # first sense only

    if not glosses:
        return None

    return {
        "type": card_type,
        "character": character,
        "romaji": romaji,
        "meaning": "; ".join(glosses[:2]),
    }


def convert(
    src: Path,
    output_dir: Path,
    common_only: bool,
    start_unit: int,
    words_per_unit: int,
    cards_per_lesson: int,
) -> None:
    data = json.loads(src.read_text(encoding="utf-8"))
    words = data.get("words", [])

    if common_only:
        words = [w for w in words if _is_common(w)]

    words.sort(key=_word_rank)

    cards = []
    for word in words:
        c = _card(word)
        if c:
            cards.append(c)

    print(f"Total cards after filtering: {len(cards)}")

    for unit_offset in range(math.ceil(len(cards) / words_per_unit)):
        unit_num  = start_unit + unit_offset
        unit_cards = cards[unit_offset * words_per_unit : (unit_offset + 1) * words_per_unit]
        unit_dir  = output_dir / "japanese" / f"unit{unit_num}"
        unit_dir.mkdir(parents=True, exist_ok=True)

        total_lessons = math.ceil(len(unit_cards) / cards_per_lesson)
        for lesson_num in range(1, total_lessons + 1):
            chunk = unit_cards[(lesson_num - 1) * cards_per_lesson : lesson_num * cards_per_lesson]
            start_rank = unit_offset * words_per_unit + (lesson_num - 1) * cards_per_lesson + 1
            lesson = {
                "unit": unit_num,
                "lesson": lesson_num,
                "title": f"Vocabulary — Frequency {start_rank}–{start_rank + len(chunk) - 1}",
                "cards": chunk,
            }
            out = unit_dir / f"lesson{lesson_num:02d}.json"
            out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"Unit {unit_num}: {len(unit_cards)} words → {total_lessons} lessons in {unit_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert jmdict-simplified JSON to lesson packs")
    parser.add_argument("--input",  required=True, type=Path,
                        help="Path to jmdict-english-common.json or jmdict-english.json")
    parser.add_argument("--output", default=Path("lessons"), type=Path,
                        help="Output root (default: lessons/)")
    parser.add_argument("--common-only", action="store_true",
                        help="Filter to words marked common (ignored if using -common.json)")
    parser.add_argument("--start-unit", default=7, type=int, metavar="N",
                        help="First unit number to write (default: 7)")
    parser.add_argument("--words-per-unit", default=200, type=int, metavar="N",
                        help="Words per unit before starting a new unit (default: 200)")
    parser.add_argument("--cards-per-lesson", default=10, type=int, metavar="N")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    convert(
        args.input, args.output, args.common_only,
        args.start_unit, args.words_per_unit, args.cards_per_lesson,
    )


if __name__ == "__main__":
    main()
