#!/usr/bin/env python3
"""
Convert HSK vocabulary JSON files into lesson packs for the learning_languages app.

Data source
-----------
Download pre-structured HSK JSON files from one of these open-source repositories:

  gigacee/hsk-vocabulary   https://github.com/gigacee/hsk-vocabulary
  Licence: CC BY-SA 4.0  (Electronic Dictionary Research and Development Group)

Expected input format — one JSON file per HSK level, e.g. hsk1.json:

  [
    {"hanzi": "爱", "pinyin": "ài", "english": "to love; love"},
    ...
  ]

Field aliases accepted: hanzi/word/simplified, pinyin/reading, english/meaning/definition.

Output
------
  lessons/mandarin/unit1/lesson01.json   (HSK 1)
  lessons/mandarin/unit2/lesson01.json   (HSK 2)
  ...
  lessons/mandarin/unit6/lesson01.json   (HSK 6)

Card format produced:
  {"type": "hanzi", "character": "爱", "romaji": "ài", "meaning": "to love; love"}

Usage
-----
  python tools/convert_hsk.py --input /path/to/hsk-vocabulary/ --output lessons/

  # override cards per lesson (default 10)
  python tools/convert_hsk.py --input /path/to/hsk-vocabulary/ --cards-per-lesson 8
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path


def _field(entry: dict, *keys: str) -> str:
    for k in keys:
        if k in entry:
            return str(entry[k]).strip()
    return ""


def _parse_level(filename: str) -> int | None:
    m = re.search(r"(\d+)", Path(filename).stem)
    return int(m.group(1)) if m else None


def convert(input_dir: Path, output_dir: Path, cards_per_lesson: int) -> None:
    input_files = sorted(input_dir.glob("hsk*.json"))
    if not input_files:
        print(f"No hsk*.json files found in {input_dir}", file=sys.stderr)
        sys.exit(1)

    for src in input_files:
        level = _parse_level(src.name)
        if level is None:
            print(f"Skipping {src.name}: cannot determine HSK level", file=sys.stderr)
            continue

        raw = json.loads(src.read_text(encoding="utf-8"))
        cards = []
        for entry in raw:
            hanzi   = _field(entry, "hanzi", "word", "simplified")
            pinyin  = _field(entry, "pinyin", "reading")
            meaning = _field(entry, "english", "meaning", "definition")
            if not hanzi:
                continue
            cards.append({"type": "hanzi", "character": hanzi, "romaji": pinyin, "meaning": meaning})

        if not cards:
            print(f"No cards parsed from {src.name}", file=sys.stderr)
            continue

        unit_dir = output_dir / "mandarin" / f"unit{level}"
        unit_dir.mkdir(parents=True, exist_ok=True)

        total_lessons = math.ceil(len(cards) / cards_per_lesson)
        for lesson_num in range(1, total_lessons + 1):
            chunk = cards[(lesson_num - 1) * cards_per_lesson : lesson_num * cards_per_lesson]
            lesson = {
                "unit": level,
                "lesson": lesson_num,
                "title": f"HSK {level} Vocabulary — Part {lesson_num}",
                "cards": chunk,
            }
            out = unit_dir / f"lesson{lesson_num:02d}.json"
            out.write_text(json.dumps(lesson, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"HSK {level}: {len(cards)} cards → {total_lessons} lessons in {unit_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert HSK JSON vocab to lesson packs")
    parser.add_argument("--input",  required=True, type=Path, help="Directory containing hsk1.json…hsk6.json")
    parser.add_argument("--output", default=Path("lessons"), type=Path, help="Output root (default: lessons/)")
    parser.add_argument("--cards-per-lesson", default=10, type=int, metavar="N")
    args = parser.parse_args()

    if not args.input.is_dir():
        print(f"Input directory not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    convert(args.input, args.output, args.cards_per_lesson)


if __name__ == "__main__":
    main()
