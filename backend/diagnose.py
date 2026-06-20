"""Diagnose why detection is or is not working, one layer at a time.

Run this first whenever detection "does nothing". It checks the Python version, the
dependency versions that actually matter (numpy 2.x silently breaks MediaPipe 0.10
and TensorFlow 2.15), that the legacy Holistic solution exists, that the camera
opens, and that a real frame produces landmarks. Each check prints OK or a specific
fix, so a silent failure becomes an actionable one.

    cd backend
    python diagnose.py            # uses camera 0
    python diagnose.py --camera 1
"""

import argparse
import platform
import sys

OK = "OK  "
BAD = "FAIL"


def check_python():
    v = sys.version_info
    print(f"{OK} python {platform.python_version()} ({platform.system()})")
    if v < (3, 10) or v >= (3, 13):
        print("     warning: this project needs Python 3.10 to 3.12. MediaPipe wheels for")
        print("     3.13+ ship only the Tasks API and drop mp.solutions.holistic.")
        return False
    return True


def check_numpy():
    try:
        import numpy as np
    except ImportError:
        print(f"{BAD} numpy not installed -> pip install -r requirements.txt")
        return False
    major = int(np.__version__.split(".")[0])
    if major >= 2:
        print(f"{BAD} numpy {np.__version__}: 2.x breaks MediaPipe 0.10 and TF 2.15.")
        print("     fix -> pip install 'numpy<2'  (then reinstall mediapipe if needed)")
        return False
    print(f"{OK} numpy {np.__version__}")
    return True


def check_mediapipe():
    try:
        import mediapipe as mp
    except Exception as e:
        print(f"{BAD} importing mediapipe failed: {e}")
        print("     fix -> pip install mediapipe==0.10.14")
        return None
    print(f"{OK} mediapipe {mp.__version__}")
    if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "holistic"):
        print(f"{BAD} mp.solutions.holistic is missing on this build (likely Python 3.13+).")
        print("     fix -> use Python 3.10 to 3.12 with mediapipe==0.10.14")
        return None
    return mp


def check_opencv():
    try:
        import cv2
        print(f"{OK} opencv {cv2.__version__}")
        return cv2
    except Exception as e:
        print(f"{BAD} importing cv2 failed: {e}")
        print("     fix -> pip install opencv-python")
        return None


def check_camera_and_detection(cv2, mp, camera):
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        print(f"{BAD} camera {camera} did not open.")
        print("     fix -> close other apps using the camera, grant camera permission,")
        print("            or try --camera 1. On macOS, allow the terminal in Privacy settings.")
        return False
    ok, frame = cap.read()
    if not ok or frame is None:
        print(f"{BAD} camera opened but returned no frame.")
        cap.release()
        return False
    print(f"{OK} camera {camera} delivered a {frame.shape[1]}x{frame.shape[0]} frame")

    from utils.landmarks import process_frame, detection_status
    import numpy as np
    detected_any = False
    with mp.solutions.holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        # Read several frames; the first few often arrive before exposure settles.
        for _ in range(15):
            ok, frame = cap.read()
            if not ok:
                continue
            vec, results = process_frame(frame, holistic)
            st = detection_status(results)
            if any(st.values()):
                detected_any = True
                nonzero = int(np.count_nonzero(vec))
                print(f"{OK} detection works: {st}, {nonzero}/192 landmark values populated")
                break
    cap.release()
    if not detected_any:
        print(f"{BAD} camera works but no landmarks were detected across 15 frames.")
        print("     This is usually lighting or framing: make sure your hands and face are")
        print("     well lit and inside the frame, then rerun. If it still fails with a good")
        print("     image, the mediapipe/numpy versions above are the next suspect.")
    return detected_any


def main():
    parser = argparse.ArgumentParser(description="Diagnose ASL detection setup")
    parser.add_argument("--camera", type=int, default=0)
    args = parser.parse_args()

    print("ASL detection diagnostics\n")
    check_python()
    check_numpy()
    mp = check_mediapipe()
    cv2 = check_opencv()
    print()
    if mp and cv2:
        ok = check_camera_and_detection(cv2, mp, args.camera)
        print("\nresult:", "detection is working." if ok else "detection is NOT working, see the FAIL lines above.")
    else:
        print("result: fix the FAIL lines above, then rerun.")


if __name__ == "__main__":
    main()
