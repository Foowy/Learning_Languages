#!/usr/bin/env python3
"""
Convert kanjidic2-simplified JSON into kanji lesson packs for learning_languages.

Data source
-----------
Download a kanjidic2-simplified release from:
  https://github.com/scriptin/jmdict-simplified/releases

  File: kanjidic2-english.json

Licence: CC BY-SA 4.0 — Electronic Dictionary Research and Development Group
  https://www.edrdg.org/edrdg/licence.html
If you distribute a lessons pack derived from this data, include the above credit.

JLPT level mapping (kanjidic2 uses the old 4-level system)
-----------------------------------------------------------
  jlptLevel 4 → JLPT N5  (~100 kanji)   → unit = start_unit + 0
  jlptLevel 3 → JLPT N4  (~200 kanji)   → unit = start_unit + 1
  jlptLevel 2 → JLPT N3  (~370 kanji)   → unit = start_unit + 2
  jlptLevel 1 → JLPT N2/N1 (~1000 kanji) → unit = start_unit + 3

Card format produced
--------------------
  {
    "type": "kanji",
    "character": "食",
    "romaji": "ショク・ジキ / た.べる・く.う",
    "meaning": "eat; food; drink"
  }

  romaji: on-yomi (katakana) before " / ", kun-yomi (hiragana+dot) after.
  Up to 3 meanings are included.

Usage
-----
  python tools/convert_kanjidic.py --input kanjidic2-english.json
  python tools/convert_kanjidic.py --input kanjidic2-english.json \\
      --output lessons/ --start-unit 3 --cards-per-lesson 10
"""

import argparse
import json
import math
import sys
from pathlib import Path


# old kanjidic2 level → (JLPT name, unit offset from start_unit)
_JLPT_LEVELS = {4: "N5", 3: "N4", 2: "N3", 1: "N2/N1"}


def _readings(groups: list, reading_type: str) -> str:
    vals = []
    for g in groups:
        for r in g.get("readings", []):
            if r.get("type") == reading_type:
                vals.append(r["value"])
    return "・".join(vals)


def _meanings(groups: list, max_count: int = 3) -> str:
    vals = []
    for g in groups:
        for m in g.get("meanings", []):
            if m.get("lang") == "en":
                vals.append(m["value"])
    return "; ".join(vals[:max_count])


def convert(src: Path, output_dir: Path, start_unit: int, cards_per_lesson: int) -> None:
    data = json.loads(src.read_text(encoding="utf-8"))
    characters = data.get("characters", [])

    # bucket by JLPT level; sort within bucket by frequency (lower = more common)
    buckets: dict[int, list] = {lvl: [] for lvl in _JLPT_LEVELS}
    skipped = 0
    for char in characters:
        level = char.get("misc", {}).get("jlptLevel")
        if level not in buckets:
            skipped += 1
            continue
        buckets[level].append(char)

    if skipped:
        print(f"Skipped {skipped} characters with no JLPT level")

    for lvl, chars in sorted(buckets.items(), reverse=True):  # 4→3→2→1
        if not chars:
            continue
        chars.sort(key=lambda c: c.get("misc", {}).get("frequency") or 9999)

        unit_num = start_unit + (4 - lvl)  # level 4 → offset 0, level 1 → offset 3
        unit_dir = output_dir / "japanese" / f"unit{unit_num}"
        unit_dir.mkdir(parents=True, exist_ok=True)

        cards = []
        for char in chars:
            rm = char.get("readingMeaning") or {}
            groups = rm.get("groups", [])
            on  = _readings(groups, "ja_on")
            kun = _readings(groups, "ja_kun")
            romaji = " / ".join(filter(None, [on, kun]))
            meaning = _meanings(groups)
            if not meaning:
                continue
            cards.append({
                "type": "kanji",
                "character": char["literal"],
                "romaji": romaji,
                "meaning": meaning,
            })

        total_lessons = math.ceil(len(cards) / cards_per_lesson)
        for lesson_num in range(1, total_lessons + 1):
            chunk = cards[(lesson_num - 1) * cards_per_lesson : lesson_num * cards_per_lesson]
            lesson = {
                "unit": unit_num,
                "lesson": lesson_num,
                "title": f"JLPT {_JLPT_LEVELS[lvl]} Kanji — Part {lesson_num}",
                "cards": chunk,
            }
            out = unit_dir / f"lesson{lesson_num:02d}.json"
            out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"JLPT {_JLPT_LEVELS[lvl]}: {len(cards)} kanji → {total_lessons} lessons in {unit_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert kanjidic2-simplified JSON to lesson packs")
    parser.add_argument("--input",  required=True, type=Path, help="Path to kanjidic2-english.json")
    parser.add_argument("--output", default=Path("lessons"), type=Path, help="Output root (default: lessons/)")
    parser.add_argument("--start-unit", default=3, type=int, metavar="N",
                        help="Unit number for JLPT N5 kanji (default: 3, after hiragana/katakana)")
    parser.add_argument("--cards-per-lesson", default=10, type=int, metavar="N")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    convert(args.input, args.output, args.start_unit, args.cards_per_lesson)


if __name__ == "__main__":
    main()
