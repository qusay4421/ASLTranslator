import json
import os
import cv2
import numpy as np
import mediapipe as mp
from pathlib import Path

import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).parent.parent))
from utils.landmarks import extract_landmarks

DATA_DIR = Path(__file__).parents[2] / "data" / "wlasl"
ANNOTATION_FILE = DATA_DIR / "WLASL_v0.3.json"
VIDEO_DIR = DATA_DIR / "videos"
OUTPUT_DIR = DATA_DIR / "sequences"
SEQUENCE_LENGTH = 30


def load_annotations() -> list:
    with open(ANNOTATION_FILE) as f:
        return json.load(f)


def extract_sequence(video_path: str, holistic) -> np.ndarray | None:
    """Extract SEQUENCE_LENGTH landmark frames from a video by uniform sampling."""
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < 5:
        cap.release()
        return None

    indices = np.linspace(0, total - 1, SEQUENCE_LENGTH, dtype=int)
    frames = []
    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return None
        frames.append(extract_landmarks(frame, holistic))
    cap.release()
    return np.array(frames)


def build_dataset(max_signs: int | None = None) -> tuple[np.ndarray, list]:
    """
    Process WLASL videos into landmark sequences.
    Saves X.npy and y.json to OUTPUT_DIR, returns (X, y_labels).
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    annotations = load_annotations()
    if max_signs:
        annotations = annotations[:max_signs]

    sequences, labels = [], []
    mp_holistic = mp.solutions.holistic

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        for entry in annotations:
            gloss = entry["gloss"]
            for instance in entry["instances"]:
                video_path = str(VIDEO_DIR / f"{instance['video_id']}.mp4")
                if not os.path.exists(video_path):
                    continue
                seq = extract_sequence(video_path, holistic)
                if seq is None:
                    continue
                sequences.append(seq)
                labels.append(gloss)
                print(f"  {gloss} / {instance['video_id']}")

    X = np.array(sequences)
    np.save(str(OUTPUT_DIR / "X.npy"), X)
    with open(str(OUTPUT_DIR / "y.json"), "w") as f:
        json.dump(labels, f)

    print(f"\nDataset: {X.shape[0]} sequences, {len(set(labels))} unique signs")
    return X, labels


if __name__ == "__main__":
    build_dataset(max_signs=50)
