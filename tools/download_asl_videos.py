"""
Download ASL videos for lesson content.

Sources:
  - Fingerspelling A-Z and numbers 1-10: Lifeprint.com (free educational use)
      https://www.lifeprint.com — Dr. Bill Vicars
  - Common signs: WLASL dataset (research/educational)
      https://github.com/dxli94/WLASL

Requirements:
  pip install httpx
  apt install ffmpeg          # GIF → MP4 conversion
  pip install yt-dlp          # YouTube clip downloads (for WLASL)

Usage:
  python3 tools/download_asl_videos.py --out /path/to/videos/asl
  python3 tools/download_asl_videos.py --out /path/to/videos/asl --skip-existing

Output filenames match the video fields in lessons/asl/:
  fs_a.mp4 … fs_z.mp4
  num_1.mp4 … num_20.mp4
  sign_hello.mp4 … etc.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

# ── Lifeprint fingerspelling GIF URLs ────────────────────────────────────────
# Educational use permitted: https://www.lifeprint.com/asl101/pages-signs/terms.htm

FS_BASE = "https://www.lifeprint.com/asl101/fingerspelling/abc-gifs"
FS_LETTERS = list("abcdefghijklmnopqrstuvwxyz")

# Numbers 1-10 from lifeprint (11-20 require a separate page; see note below)
NUM_BASE = "https://www.lifeprint.com/asl101/pages-signs/numbers"
# Numbers 1-10 GIFs follow the same abc-gifs-style path on lifeprint
NUM_URLS = {
    1:  f"{NUM_BASE}/number-1.gif",
    2:  f"{NUM_BASE}/number-2.gif",
    3:  f"{NUM_BASE}/number-3.gif",
    4:  f"{NUM_BASE}/number-4.gif",
    5:  f"{NUM_BASE}/number-5.gif",
    6:  f"{NUM_BASE}/number-6.gif",
    7:  f"{NUM_BASE}/number-7.gif",
    8:  f"{NUM_BASE}/number-8.gif",
    9:  f"{NUM_BASE}/number-9.gif",
    10: f"{NUM_BASE}/number-10.gif",
    # 11-20: teen numbers on lifeprint are on an HTML page, not direct GIFs.
    # They'll be fetched from WLASL instead (see WLASL_SIGNS below).
}

# ── WLASL gloss → output filename mapping ────────────────────────────────────
# Keys are WLASL glosses (upper-case as they appear in WLASL_v0.3.json).
# Values are our target output filenames (without .mp4).
#
# WLASL dataset: https://github.com/dxli94/WLASL
# Download WLASL_v0.3.json from that repo, then run this script with --wlasl.
# License: non-commercial research and educational use only.

WLASL_SIGNS = {
    # Numbers 11-20
    "ELEVEN":    "num_11",
    "TWELVE":    "num_12",
    "THIRTEEN":  "num_13",
    "FOURTEEN":  "num_14",
    "FIFTEEN":   "num_15",
    "SIXTEEN":   "num_16",
    "SEVENTEEN": "num_17",
    "EIGHTEEN":  "num_18",
    "NINETEEN":  "num_19",
    "TWENTY":    "num_20",
    # Greetings
    "HELLO":       "sign_hello",
    "GOODBYE":     "sign_goodbye",
    "PLEASE":      "sign_please",
    "THANK-YOU":   "sign_thank_you",
    "SORRY":       "sign_sorry",
    # Essentials
    "YES":         "sign_yes",
    "NO":          "sign_no",
    "HELP":        "sign_help",
    "STOP":        "sign_stop",
    "MORE":        "sign_more",
    # Question words
    "WHAT":        "sign_what",
    "WHERE":       "sign_where",
    "WHEN":        "sign_when",
    "WHO":         "sign_who",
    "HOW":         "sign_how",
    # Introductions
    "NAME":        "sign_my_name",       # closest WLASL gloss; no "MY NAME" compound
    "NICE-TO-MEET-YOU": "sign_nice_to_meet_you",
    "I-LOVE-YOU":  "sign_i_love_you",
    "UNDERSTAND":  "sign_understand",
    # Family
    "MOTHER":      "sign_mother",
    "FATHER":      "sign_father",
    "SISTER":      "sign_sister",
    "BROTHER":     "sign_brother",
    "BABY":        "sign_baby",
    "GRANDMOTHER": "sign_grandmother",
    "GRANDFATHER": "sign_grandfather",
    "AUNT":        "sign_aunt",
    "UNCLE":       "sign_uncle",
    "FAMILY":      "sign_family",
    # Actions
    "EAT":         "sign_eat",
    "DRINK":       "sign_drink",
    "SLEEP":       "sign_sleep",
    "WALK":        "sign_walk",
    "PLAY":        "sign_play",
    # Places
    "HOME":        "sign_home",
    "SCHOOL":      "sign_school",
    "WORK":        "sign_work",
    "STORE":       "sign_store",
    "HOSPITAL":    "sign_hospital",
    # Descriptors
    "GOOD":        "sign_good",
    "BAD":         "sign_bad",
    "BIG":         "sign_big",
    "SMALL":       "sign_small",
    "HOT":         "sign_hot",
}


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: ffmpeg not found. Install with: apt install ffmpeg", file=sys.stderr)
        sys.exit(1)


def gif_to_mp4(gif_path: Path, mp4_path: Path):
    """Convert a GIF to a looping MP4 suitable for the lesson player."""
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


def download_url(url: str, dest: Path):
    print(f"  GET {url}")
    urllib.request.urlretrieve(url, dest)


def download_fingerspelling(out_dir: Path, skip_existing: bool):
    print("\n=== Fingerspelling A-Z (Lifeprint) ===")
    check_ffmpeg()
    for letter in FS_LETTERS:
        mp4 = out_dir / f"fs_{letter}.mp4"
        if skip_existing and mp4.exists():
            print(f"  skip {mp4.name} (exists)")
            continue
        url = f"{FS_BASE}/{letter}.gif"
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_path = Path(tmp.name)
        try:
            download_url(url, gif_path)
            gif_to_mp4(gif_path, mp4)
            print(f"  → {mp4.name}")
        except Exception as e:
            print(f"  WARN: {letter} failed: {e}")
        finally:
            gif_path.unlink(missing_ok=True)


def download_numbers_lifeprint(out_dir: Path, skip_existing: bool):
    print("\n=== Numbers 1-10 (Lifeprint) ===")
    check_ffmpeg()
    for n, url in NUM_URLS.items():
        mp4 = out_dir / f"num_{n}.mp4"
        if skip_existing and mp4.exists():
            print(f"  skip {mp4.name} (exists)")
            continue
        with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmp:
            gif_path = Path(tmp.name)
        try:
            download_url(url, gif_path)
            gif_to_mp4(gif_path, mp4)
            print(f"  → {mp4.name}")
        except Exception as e:
            print(f"  WARN: num_{n} failed: {e}")
        finally:
            gif_path.unlink(missing_ok=True)


def download_wlasl_signs(out_dir: Path, wlasl_json: Path, skip_existing: bool):
    """Download sign videos from WLASL dataset video URLs using yt-dlp."""
    try:
        import subprocess
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("ERROR: yt-dlp not found. Install with: pip install yt-dlp", file=sys.stderr)
        return

    print(f"\n=== Signs & Numbers 11-20 (WLASL: {wlasl_json}) ===")
    data = json.loads(wlasl_json.read_text())
    # Index by gloss
    index = {entry["gloss"].upper(): entry for entry in data}

    for gloss, stem in WLASL_SIGNS.items():
        mp4 = out_dir / f"{stem}.mp4"
        if skip_existing and mp4.exists():
            print(f"  skip {mp4.name} (exists)")
            continue

        entry = index.get(gloss)
        if not entry:
            print(f"  WARN: '{gloss}' not found in WLASL dataset")
            continue

        # Pick first instance with a url
        url = None
        for instance in entry.get("instances", []):
            if instance.get("url"):
                url = instance["url"]
                break

        if not url:
            print(f"  WARN: no URL for '{gloss}'")
            continue

        print(f"  {gloss} → {mp4.name}  ({url})")
        result = subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-f", "mp4/bestvideo[ext=mp4]",
                "-o", str(mp4),
                url,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  WARN: yt-dlp failed for '{gloss}': {result.stderr.strip()[:120]}")


def main():
    parser = argparse.ArgumentParser(description="Download ASL videos for lesson content")
    parser.add_argument("--out", required=True, help="Output directory (e.g. /data/videos/asl)")
    parser.add_argument("--wlasl", metavar="JSON", help="Path to WLASL_v0.3.json for common signs")
    parser.add_argument("--skip-existing", action="store_true", help="Skip files that already exist")
    parser.add_argument(
        "--only",
        choices=["fs", "numbers", "signs"],
        help="Download only one category instead of all",
    )
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    only = args.only

    if only in (None, "fs"):
        download_fingerspelling(out_dir, args.skip_existing)

    if only in (None, "numbers"):
        download_numbers_lifeprint(out_dir, args.skip_existing)

    if only in (None, "signs"):
        if not args.wlasl:
            print(
                "\nSkipping common signs: pass --wlasl WLASL_v0.3.json to download them.\n"
                "Get the file from: https://github.com/dxli94/WLASL"
            )
        else:
            download_wlasl_signs(out_dir, Path(args.wlasl), args.skip_existing)

    print("\nDone.")


if __name__ == "__main__":
    main()
