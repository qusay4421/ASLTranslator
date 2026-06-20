# DEVLOG

Newest entry on top.

## 2026-06-20 — Fix: detection "never worked"

### Diagnosis
Two causes, both consistent with detection silently doing nothing:
1. The original code never drew landmarks (the old `landmarks.py` main showed the raw
   webcam with no overlay), so working detection looked like nothing was happening.
2. `requirements.txt` pinned MediaPipe 0.10.14 and TensorFlow 2.15 but left numpy
   unpinned, so pip installed numpy 2.x. Both libraries require numpy < 2; the
   mismatch makes detection install cleanly and then produce no landmarks (or crash).
   protobuf 5.x causes the same class of breakage.

### Did
- Pinned the dependency stack in `requirements.txt`: `numpy==1.26.4` and
  `protobuf>=3.20,<5`, with a comment explaining why. This is the most likely fix.
- Added `backend/diagnose.py`: a layered self-test that checks Python version, numpy
  and MediaPipe versions, that `mp.solutions.holistic` exists, that the camera opens
  and returns a frame, and that a real frame produces landmarks. Each failure prints a
  specific fix, so a silent failure becomes an actionable one.
- `app.py` now shows a clear on-screen hint after about 5 seconds with no detection,
  so a setup problem is visible instead of looking like the app does nothing. The
  per-component status readout (added earlier) already shows which parts are detected.

### Verified
- All files compile; preprocessing tests still pass (6/6).
- Could not run the camera/MediaPipe path here (build box is Python 3.14 with no GL
  libs and a Tasks-only MediaPipe wheel). On your machine, run `python diagnose.py`
  first: it will confirm the fix or point at the exact remaining problem.

### If it still fails after this
Run `python diagnose.py` and share the output. The most likely remaining causes it
will surface are camera permissions (especially macOS) or a wrong Python version. If
the versions are right and the camera works but landmarks still do not appear, the
next step is porting detection to MediaPipe's current Tasks API.

## 2026-06-19 — Standalone real-time detection app, drawing, and data collection

### Did
- Added live landmark drawing to `backend/utils/landmarks.py`: `draw_landmarks`
  renders hands, face, and pose, `process_frame` returns the 192-value vector and the
  raw results from a single inference pass, and `detection_status` reports which
  components were found. `extract_landmarks` is unchanged in signature, so the
  WebSocket backend keeps working.
- Added `backend/app.py`, a standalone desktop app: webcam in, Holistic detection,
  landmarks drawn live, an on-screen readout of which parts are detected, and FPS.
  With `--translate` it also loads the trained model and overlays the predicted sign,
  confidence, and running sentence. Detection-only is the default and does not import
  TensorFlow.
- Added `backend/collect.py`, a webcam data-collection tool. It records takes of a
  sign (30 frames each), converts them to landmark vectors, and appends to the same
  `data/wlasl/sequences/X.npy` and `y.json` that `model/train.py` reads, saving after
  every take. This is how to grow past the current 10 signs.
- Added `backend/tests/test_preprocess.py`, pure-numpy tests for the normalize and
  pad/trim logic (no MediaPipe or TensorFlow needed). 6/6 pass.
- Noted the Python 3.10 to 3.12 requirement in `requirements.txt` and ignored the
  generated `/data/` directory.

### Verified
- All changed Python files compile (`py_compile`).
- The preprocessing tests pass under numpy.
- Note: MediaPipe Holistic and the TensorFlow model could not be run in the build
  environment (Python 3.14 there ships only MediaPipe's Tasks API, not the legacy
  `mp.solutions.holistic` this project uses). The camera path, drawing, and live
  translation need to be run on a Python 3.10 to 3.12 setup. See "How to run" below.

### How to run
```sh
cd backend
python -m venv venv && source venv/bin/activate   # Python 3.10 to 3.12
pip install -r requirements.txt

python app.py                 # detection only: hands, face, pose drawn live
python app.py --translate     # also overlay sign predictions (needs model/model.keras)

# add a new sign, then retrain:
python collect.py --label hello --takes 30
python model/train.py
```

### Needs work / next up
- Run `app.py` on a real webcam to confirm detection draws and FPS is usable; tune
  Holistic confidence and model complexity if needed.
- The current model covers 10 signs; collect more takes per sign (and more signs) to
  improve robustness, then retrain.
- Prediction smoothing: the sliding window can flicker between signs; consider
  debouncing on N consecutive agreeing predictions before committing a word.
- Wire the standalone detection overlay into the Electron front end so the video-call
  product shows the same translation.
