# DEVLOG

Newest entry on top. Each entry: **Did**, **Why**, **Needs work / next up**.

---

## 2026-06-04 — Preprocessing unit tests + CI

**Did**
- Added `backend/tests/test_preprocess.py` — 11 unit tests covering the pure landmark pipeline in `utils/preprocess.py`: `normalize_landmarks` (unit-range scaling, the constant-frame divide-by-zero guard, shape preservation), `pad_or_trim` (front zero-padding, exact-length passthrough, most-recent-frame trimming, return type), and `build_input` (the `(1, 30, 192)` batch tensor shape and per-frame normalization bounds).
- Added `backend/pytest.ini` (`pythonpath=.`, `testpaths=tests`) so `from utils.preprocess import ...` resolves without an editable install.
- Added `.github/workflows/ci.yml` — runs the suite on push/PR to `master` under Python 3.10, installing only `numpy`+`pytest` (no TensorFlow/MediaPipe needed since these tests are pure-numpy).

**Why**
- The preprocessing layer defines the tensor contract (`30 × 192`) that `model/predict.py` and the trained LSTM depend on. A silent change to padding direction or normalization would corrupt inference with no error. These tests lock that contract in, and CI makes regressions visible on every PR — the repo had no automated tests before this.
- Started with `preprocess.py` because it is dependency-light and deterministic: high value, zero risk to the live app.

**Verified**
- `python3 -m py_compile` on the test file and `preprocess.py` — OK.
- `ci.yml` validated with PyYAML; `pytest.ini` parsed. Tests were authored by tracing each assertion against the implementation by hand. Could not execute `pytest` locally (this box has no pip/numpy and no ensurepip) — the GitHub Actions workflow runs them on a clean Python 3.10 where numpy installs normally.

**Needs work / next up**
- Add tests for `model/predict.py` sentence-buffer/debounce logic (`last_sign` dedup, `CONFIDENCE_THRESHOLD` gating, `SENTENCE_MAX` rollover). Needs the TF model import mocked/stubbed so it runs without `model.keras`.
- `utils/landmarks.py` `extract_landmarks` — test the zero-fill fallbacks (missing hands/face/pose) using a fake `holistic` results object; verify the output is always exactly 192 values.
- Reconcile a spec/code mismatch: `CLAUDE.md` lists `tensorflow==2.21` in prose but `requirements.txt` pins `2.15.0`. Pick one.
- `SEQUENCE_LENGTH` is defined in both `preprocess.py` and `predict.py` — consider a single source of truth.
- Consider prediction confidence smoothing/debounce (e.g. require N consecutive agreeing frames before emitting a sign) to reduce overlay flicker.
