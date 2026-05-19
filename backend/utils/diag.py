import cv2
import json
from pathlib import Path

VIDEO_DIR = Path(__file__).parents[2] / "data" / "wlasl" / "videos"
ANN_FILE = Path(__file__).parents[2] / "data" / "wlasl" / "WLASL_v0.3.json"

with open(ANN_FILE) as f:
    annotations = json.load(f)

checked = 0
for entry in annotations[:10]:
    for inst in entry["instances"][:10]:
        vid_id = inst["video_id"]
        vid = VIDEO_DIR / f"{vid_id}.mp4"
        if vid.exists():
            cap = cv2.VideoCapture(str(vid))
            frames = 0
            while True:
                ret, _ = cap.read()
                if not ret:
                    break
                frames += 1
            cap.release()
            size_kb = vid.stat().st_size // 1024
            print(f"{vid.name}: {frames} frames ({size_kb} KB)")
            checked += 1
            if checked >= 8:
                break
    if checked >= 8:
        break

print(f"\nChecked {checked} videos")
