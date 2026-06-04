# ASLTranslator

Real-time American Sign Language translation built into a video call. ASLTranslator captures webcam frames, extracts hand/face/pose landmarks with MediaPipe, classifies sign sequences with a trained LSTM, and overlays the translated text live during a WebRTC call — think FaceTime with an ASL interpreter built in.

> Status: early but working. The backend runs live inference over a WebSocket and the model currently recognizes **10 signs** (`before, book, candy, chair, clothes, computer, cousin, drink, go, who`), with the [WLASL](https://github.com/dxli94/WLASL) dataset as the path to scaling vocabulary.

---

## How it works

```
Webcam ─▶ Electron/React frontend ──(frames over WebSocket)──▶ FastAPI backend
                  ▲                                                   │
                  │                                          MediaPipe Holistic
            translated text                                  (hand+face+pose landmarks)
            overlay on video                                          │
                  │                                            LSTM classifier (Keras)
                  └───────────────(predicted sign text)───────────────┘
```

1. **Capture** — the Electron desktop app streams webcam frames (and peer video via WebRTC/PeerJS).
2. **Landmarks** — `backend/utils/landmarks.py` runs MediaPipe Holistic to extract 21×2 hand, 468 face, and pose landmarks per frame.
3. **Preprocess** — `backend/utils/preprocess.py` normalizes and flattens landmarks into fixed-length sequences.
4. **Classify** — `backend/model/predict.py` runs a sliding-window LSTM (`model.keras`) to predict the sign.
5. **Translate** — predicted text streams back over the WebSocket and renders as a live overlay (`Translator.jsx`).

## Tech stack

| Layer | Tools |
|---|---|
| Frontend | Electron, React, Vite, WebRTC (PeerJS), socket.io-client |
| Backend | Python 3.10, FastAPI + Uvicorn, WebSockets |
| ML / CV | MediaPipe Holistic, TensorFlow/Keras (LSTM), OpenCV, NumPy, scikit-learn |
| Dataset | WLASL (Word-Level ASL) |

## Project structure

```
ASLTranslator/
├── backend/
│   ├── main.py              # FastAPI app + WebSocket inference server
│   ├── model/
│   │   ├── train.py         # LSTM training
│   │   ├── predict.py       # sliding-window inference
│   │   ├── model.keras      # trained model
│   │   └── labels.json      # sign index → label map
│   └── utils/
│       ├── landmarks.py     # MediaPipe landmark extraction
│       ├── preprocess.py    # normalize/flatten landmarks
│       └── dataset.py       # WLASL loader / sequence builder
└── frontend/
    ├── main.js              # Electron main process
    └── src/
        ├── App.jsx
        └── components/      # VideoCall, Translator, Controls
```

## Getting started

### Backend

```bash
cd backend
python3.10 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload          # serves WebSocket at ws://localhost:8000/ws
```

Health check: `curl http://localhost:8000/health` → `{"status":"ok"}`

### Frontend

```bash
cd frontend
npm install
npm run dev                        # launches Vite + Electron
```

## Roadmap

- Expand vocabulary beyond the current 10 signs toward the full WLASL set
- Confidence smoothing / debouncing on predictions to reduce flicker
- Word-to-sentence assembly with simple grammar handling
- Automated tests for the landmark + preprocessing pipeline
- Packaged desktop builds (electron-builder) for macOS/Windows

## License

See repository for license details.
