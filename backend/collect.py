"""Record labeled landmark sequences from the webcam to grow the training set.

For a given sign label, this captures several takes of SEQUENCE_LENGTH frames each,
turns every frame into the 192-value landmark vector, and appends them to the same
X.npy / y.json that train.py reads. So the workflow to add a sign is: run this, then
run model/train.py.

Example:
    python collect.py --label hello --takes 30
    python collect.py --label thanks --takes 30
    python model/train.py

Keys during capture: space starts the next take, q quits early (progress is saved).
"""

import argparse
import json
import time
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

from utils.landmarks import process_frame, draw_landmarks, detection_status
from utils.preprocess import SEQUENCE_LENGTH, LANDMARK_DIM

mp_holistic = mp.solutions.holistic

SEQUENCE_DIR = Path(__file__).parents[1] / "data" / "wlasl" / "sequences"
X_PATH = SEQUENCE_DIR / "X.npy"
Y_PATH = SEQUENCE_DIR / "y.json"


def load_existing():
    """Load the current dataset, or empty arrays if this is the first collection.

    Appending to what exists means collecting a new sign never discards earlier ones.
    """
    if X_PATH.exists() and Y_PATH.exists():
        X = list(np.load(str(X_PATH)))
        with open(Y_PATH) as f:
            y = json.load(f)
        return X, y
    return [], []


def save(X, y):
    SEQUENCE_DIR.mkdir(parents=True, exist_ok=True)
    np.save(str(X_PATH), np.array(X))
    with open(Y_PATH, "w") as f:
        json.dump(y, f)


def banner(image, text, color=(255, 255, 255)):
    h, w = image.shape[:2]
    cv2.rectangle(image, (0, 0), (w, 40), (0, 0, 0), cv2.FILLED)
    cv2.putText(image, text, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)


def main():
    parser = argparse.ArgumentParser(description="Collect landmark sequences for a sign")
    parser.add_argument("--label", required=True, help="sign label to record")
    parser.add_argument("--takes", type=int, default=30, help="number of sequences to record")
    parser.add_argument("--camera", type=int, default=0, help="camera index")
    args = parser.parse_args()

    X, y = load_existing()
    print(f"existing samples: {len(X)} | recording {args.takes} takes of '{args.label}'")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {args.camera}")

    recorded = 0
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while recorded < args.takes:
            # Idle until the user is ready, so each take starts deliberately rather
            # than mid-motion.
            if not wait_for_start(cap, holistic, args.label, recorded, args.takes):
                break

            sequence = countdown_and_capture(cap, holistic, args.label, recorded, args.takes)
            if sequence is None:
                break
            X.append(sequence)
            y.append(args.label)
            recorded += 1
            save(X, y)  # save after every take so a crash never loses prior work

    cap.release()
    cv2.destroyAllWindows()
    print(f"done. recorded {recorded} takes. dataset now {len(X)} samples across {len(set(y))} labels.")


def wait_for_start(cap, holistic, label, recorded, takes):
    """Show the live view until the user presses space (returns True) or q (False)."""
    while True:
        ok, frame = cap.read()
        if not ok:
            return False
        frame = cv2.flip(frame, 1)
        _, results = process_frame(frame, holistic)
        draw_landmarks(frame, results)
        st = detection_status(results)
        ready = st["left_hand"] or st["right_hand"]
        msg = f"'{label}'  take {recorded + 1}/{takes}  -  SPACE to record, q to quit"
        banner(frame, msg, (0, 220, 0) if ready else (0, 180, 220))
        cv2.imshow("Collect", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            return True
        if key == ord("q"):
            return False


def countdown_and_capture(cap, holistic, label, recorded, takes):
    """Count down, then capture exactly SEQUENCE_LENGTH frames of landmark vectors."""
    for n in (3, 2, 1):
        t0 = time.time()
        while time.time() - t0 < 0.6:
            ok, frame = cap.read()
            if not ok:
                return None
            frame = cv2.flip(frame, 1)
            _, results = process_frame(frame, holistic)
            draw_landmarks(frame, results)
            banner(frame, f"recording in {n}...", (0, 180, 255))
            cv2.imshow("Collect", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                return None

    sequence = []
    while len(sequence) < SEQUENCE_LENGTH:
        ok, frame = cap.read()
        if not ok:
            return None
        frame = cv2.flip(frame, 1)
        vec, results = process_frame(frame, holistic)
        sequence.append(vec)
        draw_landmarks(frame, results)
        banner(frame, f"REC '{label}'  {len(sequence)}/{SEQUENCE_LENGTH}", (0, 0, 255))
        cv2.imshow("Collect", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            return None

    assert len(sequence) == SEQUENCE_LENGTH
    assert len(sequence[0]) == LANDMARK_DIM
    return sequence


if __name__ == "__main__":
    main()
