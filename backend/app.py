"""Standalone real-time ASL detection and translation app.

Opens the webcam, runs MediaPipe Holistic, draws hand, face, and pose landmarks
live, and (optionally) overlays sign predictions from the trained model. This is the
quickest way to see the detection working end to end without the Electron front end.

Run detection only (no TensorFlow needed):
    python app.py

Run with live translation (needs model/model.keras and a TF install):
    python app.py --translate

Keys: q quits, c clears the translated sentence.
"""

import argparse
import time

import cv2
import mediapipe as mp

from utils.landmarks import process_frame, draw_landmarks, detection_status

mp_holistic = mp.solutions.holistic

GREEN = (0, 200, 0)
GREY = (120, 120, 120)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def draw_hud(image, status, fps, translation):
    """Overlay detection status, FPS, and any translation onto the frame."""
    h, w = image.shape[:2]

    # Per-component detection readout: green when present, grey when missing, so it
    # is obvious at a glance whether hands and face are being picked up.
    x = 10
    for name in ("left_hand", "right_hand", "face", "pose"):
        color = GREEN if status[name] else GREY
        label = name.replace("_", " ")
        cv2.putText(image, label, (x, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        x += 130

    cv2.putText(image, f"{fps:4.1f} FPS", (w - 110, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, WHITE, 1, cv2.LINE_AA)

    if translation is not None:
        # A filled strip keeps the caption readable over a busy background.
        cv2.rectangle(image, (0, h - 50), (w, h), BLACK, cv2.FILLED)
        cv2.putText(image, translation, (12, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, WHITE, 2, cv2.LINE_AA)


def main():
    parser = argparse.ArgumentParser(description="Real-time ASL detection and translation")
    parser.add_argument("--camera", type=int, default=0, help="camera index")
    parser.add_argument("--translate", action="store_true",
                        help="run the trained model and overlay predictions")
    parser.add_argument("--no-mirror", action="store_true",
                        help="do not mirror the camera (mirroring is the natural selfie view)")
    args = parser.parse_args()

    predictor = None
    if args.translate:
        # Import lazily so detection-only mode never has to load TensorFlow, which is
        # heavy and may not be installed.
        try:
            from model.predict import SignPredictor
            predictor = SignPredictor()
        except Exception as e:
            print(f"Translation disabled (could not load model): {e}")

    cap = cv2.VideoCapture(args.camera)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera {args.camera}")

    prev = time.time()
    fps = 0.0
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if not args.no_mirror:
                frame = cv2.flip(frame, 1)

            vec, results = process_frame(frame, holistic)
            draw_landmarks(frame, results)

            translation = None
            if predictor is not None:
                predictor.add_frame(vec)
                result = predictor.predict()
                if result:
                    translation = f"{result['sentence']}   ({result['sign']} {result['confidence']:.0%})"
                else:
                    translation = ""

            # Smooth the FPS readout so it does not flicker frame to frame.
            now = time.time()
            dt = now - prev
            prev = now
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)

            draw_hud(frame, detection_status(results), fps, translation)
            cv2.imshow("ASL Translator", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("c") and predictor is not None:
                predictor.sentence.clear()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
