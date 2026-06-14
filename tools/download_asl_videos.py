"""
Download ASL videos for lesson content.

Sources:
  - Fingerspelling A-Z: Lifeprint.com (free educational use)
      https://www.lifeprint.com — Dr. Bill Vicars
  - Numbers + common signs: SpreadTheSign.com (ASL, language 13)
      Searches by word, fetches direct MP4 from word page.

Requirements:
  apt install ffmpeg          # GIF -> MP4 conversion (fingerspelling only)

Usage:
  python3 tools/download_asl_videos.py --out /path/to/videos/asl
  python3 tools/download_asl_videos.py --out /path/to/videos/asl --skip-existing
  python3 tools/download_asl_videos.py --out /path/to/videos/asl --only fs
  python3 tools/download_asl_videos.py --out /path/to/videos/asl --only signs

Output filenames match the video fields in lessons/asl/:
  fs_a.mp4 ... fs_z.mp4
  num_1.mp4 ... num_20.mp4
  sign_hello.mp4 ... etc.
"""

import argparse
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# ── Lifeprint fingerspelling ─────────────────────────────────────────────────
# Educational use: https://www.lifeprint.com
FS_BASE = "https://www.lifeprint.com/asl101/fingerspelling/abc-gifs"
FS_LETTERS = list("abcdefghijklmnopqrstuvwxyz")

# ── SpreadTheSign search terms for each output filename ─────────────────────
# Value is the search query sent to spreadthesign.com/en.us/search/?q=...
# Language 13 = ASL (American English).
STS_SIGNS = {
    # Numbers
    "num_1":  "one",
    "num_2":  "two",
    "num_3":  "three",
    "num_4":  "four",
    "num_5":  "five",
    "num_6":  "six",
    "num_7":  "seven",
    "num_8":  "eight",
    "num_9":  "nine",
    "num_10": "ten",
    "num_11": "eleven",
    "num_12": "twelve",
    "num_13": "thirteen",
    "num_14": "fourteen",
    "num_15": "fifteen",
    "num_16": "sixteen",
    "num_17": "seventeen",
    "num_18": "eighteen",
    "num_19": "nineteen",
    "num_20": "twenty",
    # Greetings
    "sign_hello":     "hello",
    "sign_goodbye":   "goodbye",
    "sign_please":    "please",
    "sign_thank_you": "thank you",
    "sign_sorry":     "sorry",
    # Essentials
    "sign_yes":  "yes",
    "sign_no":   "no",
    "sign_help": "help",
    "sign_stop": "stop",
    "sign_more": "more",
    # Question words
    "sign_what":  "what",
    "sign_where": "where",
    "sign_when":  "when",
    "sign_who":   "who",
    "sign_how":   "how",
    # Introductions
    "sign_my_name":          "name",
    "sign_your_name":        "name",       # same sign, duplicate file ok
    "sign_nice_to_meet_you": "nice to meet you",
    "sign_i_love_you":       "i love you",
    "sign_understand":       "understand",
    # Family
    "sign_mother":      "mother",
    "sign_father":      "father",
    "sign_sister":      "sister",
    "sign_brother":     "brother",
    "sign_baby":        "baby",
    "sign_grandmother": "grandmother",
    "sign_grandfather": "grandfather",
    "sign_aunt":        "aunt",
    "sign_uncle":       "uncle",
    "sign_family":      "family",
    # Actions
    "sign_eat":   "eat",
    "sign_drink": "drink",
    "sign_sleep": "sleep",
    "sign_walk":  "walk",
    "sign_play":  "play",
    # Places
    "sign_home":     "home",
    "sign_school":   "school",
    "sign_work":     "work",
    "sign_store":    "store",
    "sign_hospital": "hospital",
    # Descriptors
    "sign_good":  "good",
    "sign_bad":   "bad",
    "sign_big":   "big",
    "sign_small": "small",
    "sign_hot":   "hot",
}

STS_BASE = "https://www.spreadthesign.com"
STS_MEDIA = "https://media.spreadthesign.com"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; asl-lesson-downloader/1.0)"}

# Direct word-page fallbacks for signs whose search returns wrong results.
# Each value is (word_id, slug) for spreadthesign.com/en.us/word/{id}/{slug}/
STS_FALLBACKS: dict[str, tuple[str, str]] = {
    "sign_hello":            ("5538",  "hello"),
    "sign_goodbye":          ("10855", "bye-bye"),
    "sign_thank_you":        ("4017",  "grateful"),
    "sign_nice_to_meet_you": ("1744",  "meet"),
    "sign_i_love_you":       ("4058",  "love"),
    "sign_work":             ("1",     "work"),
}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read()


def _sts_mp4_from_word_page(word_id: str, slug: str) -> str | None:
    """Fetch a SpreadTheSign word page and return the ASL MP4 URL, or None."""
    html = _get(f"{STS_BASE}/en.us/word/{word_id}/{slug}/").decode("utf-8", errors="replace")
    mp4 = re.search(r'media\.spreadthesign\.com/video/mp4/13/(\d+)\.mp4', html)
    return f"{STS_MEDIA}/video/mp4/13/{mp4.group(1)}.mp4" if mp4 else None


def sts_lookup(stem: str, query: str) -> str | None:
    """Return direct MP4 URL for a sign via SpreadTheSign, or None."""
    # Try known-good word page first
    if stem in STS_FALLBACKS:
        word_id, slug = STS_FALLBACKS[stem]
        url = _sts_mp4_from_word_page(word_id, slug)
        if url:
            return url

    # Fall back to search
    q = urllib.parse.quote_plus(query)
    html = _get(f"{STS_BASE}/en.us/search/?q={q}").decode("utf-8", errors="replace")
    m = re.search(r'/en\.us/word/(\d+)/([^/"]+)/', html)
    if not m:
        return None
    url = _sts_mp4_from_word_page(m.group(1), m.group(2))
    return url


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: ffmpeg not found. Install with: apt install ffmpeg", file=sys.stderr)
        sys.exit(1)


def gif_to_mp4(gif_path: Path, mp4_path: Path):
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(gif_path),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=15",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(mp4_path),
        ],
        capture_output=True,
        check=True,
    )


def download_fingerspelling(out_dir: Path, skip_existing: bool):
    print("\n=== Fingerspelling A-Z (Lifeprint) ===")
    check_ffmpeg()
    for letter in FS_LETTERS:
        mp4 = out_dir / f"fs_{letter}.mp4"
        if skip_existing and mp4.exists():
            print(f"  skip {mp4.name}")
            continue
        url = f"{FS_BASE}/{letter}.gif"
        print(f"  {letter.upper()}  {url}")
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_path = Path(tmp.name)
        try:
            data = _get(url)
            gif_path.write_bytes(data)
            gif_to_mp4(gif_path, mp4)
            print(f"      → {mp4.name}")
        except Exception as e:
            print(f"      WARN: failed: {e}")
        finally:
            gif_path.unlink(missing_ok=True)


def download_sts_signs(out_dir: Path, skip_existing: bool):
    print("\n=== Numbers + Signs (SpreadTheSign / ASL) ===")
    ok = fail = 0
    for stem, query in STS_SIGNS.items():
        mp4 = out_dir / f"{stem}.mp4"
        if skip_existing and mp4.exists():
            print(f"  skip {mp4.name}")
            ok += 1
            continue
        try:
            video_url = sts_lookup(stem, query)
            if not video_url:
                print(f"  MISS  {stem!r:30s} ('{query}' — no ASL video found)")
                fail += 1
                continue
            data = _get(video_url)
            mp4.write_bytes(data)
            print(f"  OK    {stem!r:30s} ({query})")
            ok += 1
            time.sleep(0.3)   # be polite
        except Exception as e:
            print(f"  FAIL  {stem!r:30s}: {e}")
            fail += 1

    print(f"\n  {ok} downloaded, {fail} missed")


def main():
    # urllib.parse needed for quote_plus — import here to avoid top-level dep confusion
    global urllib
    import urllib.parse

    parser = argparse.ArgumentParser(description="Download ASL videos for lesson content")
    parser.add_argument("--out", required=True, help="Output directory (e.g. /data/videos/asl)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files that already exist")
    parser.add_argument(
        "--only", choices=["fs", "signs"],
        help="Download only fingerspelling or only signs/numbers",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.only in (None, "fs"):
        download_fingerspelling(out_dir, args.skip_existing)

    if args.only in (None, "signs"):
        download_sts_signs(out_dir, args.skip_existing)

    print("\nDone.")


if __name__ == "__main__":
    main()
