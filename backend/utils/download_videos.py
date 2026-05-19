"""
Download WLASL videos for a subset of signs.
Handles direct MP4 URLs and YouTube URLs via yt-dlp.
Run from backend/ with venv active.
"""

import json
import os
import time
import urllib.request
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "data" / "wlasl"
ANNOTATION_FILE = DATA_DIR / "WLASL_v0.3.json"
VIDEO_DIR = DATA_DIR / "videos"

YOUTUBE_DOMAINS = ("youtube.com", "youtu.be")


def is_youtube(url: str) -> bool:
    return any(d in url for d in YOUTUBE_DOMAINS)


def download_direct(url: str, dest: Path) -> bool:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r, open(dest, "wb") as f:
            f.write(r.read())
        return dest.stat().st_size > 10_000
    except Exception as e:
        print(f"    direct download failed: {e}")
        return False


def download_youtube(url: str, video_id: str, dest_dir: Path) -> bool:
    try:
        import yt_dlp
        ydl_opts = {
            "outtmpl": str(dest_dir / f"{video_id}.%(ext)s"),
            "format": "mp4/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return (dest_dir / f"{video_id}.mp4").exists()
    except Exception as e:
        print(f"    yt-dlp failed: {e}")
        return False


def download_dataset(max_signs: int = 10, max_videos_per_sign: int = 10):
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    with open(ANNOTATION_FILE) as f:
        annotations = json.load(f)

    total_ok, total_fail = 0, 0

    for entry in annotations[:max_signs]:
        gloss = entry["gloss"]
        print(f"\n[{gloss}]")
        ok = 0
        for inst in entry["instances"][:max_videos_per_sign]:
            video_id = inst["video_id"]
            url = inst.get("url", "")
            dest = VIDEO_DIR / f"{video_id}.mp4"

            if dest.exists() and dest.stat().st_size > 10_000:
                print(f"  {video_id}: already exists")
                ok += 1
                continue

            print(f"  {video_id}: {url[:60]}...")
            if is_youtube(url):
                success = download_youtube(url, video_id, VIDEO_DIR)
            else:
                success = download_direct(url, dest)

            if success:
                print(f"    OK ({dest.stat().st_size // 1024} KB)")
                ok += 1
            else:
                print(f"    SKIP")
                total_fail += 1

            time.sleep(0.3)

        total_ok += ok
        print(f"  -> {ok} videos for '{gloss}'")

    print(f"\nDone: {total_ok} downloaded, {total_fail} failed")


if __name__ == "__main__":
    download_dataset(max_signs=10, max_videos_per_sign=10)
