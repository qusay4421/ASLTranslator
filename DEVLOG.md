# ASLTranslator — Dev Log

Running log of incremental work. Newest entries on top. Each entry: what changed, why, and what still needs work.

---

## 2026-06-04 — Project README + dev log

**Did:**
- Added a proper `README.md`: project pitch, architecture diagram, data-flow walkthrough, tech-stack table, project structure, and backend/frontend run instructions.
- Documented current model state accurately (10 trained signs) and a roadmap.
- Started this `DEVLOG.md` to track day-by-day progress.

**Why:** The repo had no README — first thing a recruiter or collaborator sees. Zero-risk, high-visibility starting point before touching code.

**Needs work / next up:**
- No automated tests anywhere yet — the landmark/preprocess pipeline (`utils/preprocess.py`, `utils/landmarks.py`) is pure-ish and very testable. Good next increment.
- `CLAUDE.md` spec lists TensorFlow 2.21 but `requirements.txt` pins 2.15.0 — reconcile.
- Prediction overlay reportedly flickers; needs confidence smoothing/debounce.
- Vocabulary is only 10 signs; scaling to WLASL needs the dataset pipeline exercised end-to-end.

---
