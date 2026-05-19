# ASLTranslator — Project Specification

## Overview
A real-time American Sign Language (ASL) translator integrated into a video calling application. The app detects hand gestures and facial expressions via webcam, classifies them as ASL signs using a trained LSTM model, and displays translated text as an overlay during video calls.

---

## Tech Stack

### Backend (Python 3.10)
- **MediaPipe Holistic** — extracts hand landmarks (21 points x2), face landmarks (468 points), and pose landmarks per frame
- **TensorFlow 2.21 / Keras** — LSTM model trained on landmark sequences for sign classification
- **FastAPI + Uvicorn** — WebSocket server that receives frames from Electron, runs inference, and streams back translated text
- **OpenCV** — camera capture and frame preprocessing
- **NumPy** — landmark array manipulation

### Frontend (Node 24 / Electron)
- **Electron** — cross-platform desktop app shell
- **React + Vite** — UI framework
- **WebRTC** — peer-to-peer video calling
- **Socket.io-client** — communicates with Python backend over WebSocket

### Dataset
- **WLASL (Word-Level ASL)** — 2000+ signs, 21,000+ videos
- Source: https://github.com/dxli94/WLASL
- Stored in: /data/wlasl/

---

## Folder Structure

    ASLTranslator/
    ├── CLAUDE.md
    ├── README.md
    ├── .gitignore
    ├── venv/                        # Python 3.10 virtual environment
    ├── backend/
    │   ├── main.py                  # FastAPI app entry point, WebSocket server
    │   ├── requirements.txt         # pip dependencies
    │   ├── model/
    │   │   ├── train.py             # LSTM model training script
    │   │   ├── predict.py           # Inference logic, sliding window classifier
    │   │   ├── model.keras          # Saved trained model (generated after training)
    │   │   └── labels.json          # Sign label index map (generated after training)
    │   └── utils/
    │       ├── landmarks.py         # MediaPipe Holistic landmark extraction
    │       ├── preprocess.py        # Normalize/flatten landmarks into numpy arrays
    │       └── dataset.py           # WLASL dataset loader and sequence builder
    ├── frontend/
    │   ├── package.json
    │   ├── vite.config.js
    │   ├── index.html
    │   ├── main.js                  # Electron main process
    │   ├── preload.js               # Electron preload script (context bridge)
    │   └── src/
    │       ├── main.jsx             # React entry point
    │       ├── App.jsx              # Root component, manages app state
    │       └── components/
    │           ├── VideoCall.jsx    # WebRTC video call UI
    │           ├── Translator.jsx   # ASL translation overlay
    │           └── Controls.jsx     # Mute, camera toggle, call controls
    └── data/
        └── wlasl/
            ├── WLASL_v0.3.json      # Annotation file
            └── videos/              # Raw video files per sign

---

## Architecture

    Webcam frames
         ↓
    MediaPipe Holistic (landmarks.py)
         ↓
    Normalize + flatten landmarks (preprocess.py)
         ↓
    Sliding window buffer (30 frames)
         ↓
    LSTM model inference (predict.py)
         ↓
    Classified sign + confidence score
         ↓
    FastAPI WebSocket (main.py)
         ↓
    Electron frontend (Socket.io)
         ↓
    Translation overlay on video call UI

---

## Model Architecture

- **Input:** 30 frames x N landmarks flattened to 1D vector per frame
- **Landmark composition per frame:**
  - Left hand: 21 points x 3 (x, y, z) = 63
  - Right hand: 21 points x 3 = 63
  - Face (key points only): 10 points x 3 = 30
  - Pose (upper body): 12 points x 3 = 36
  - **Total per frame: 192 values**
- **Model layers:**
  - LSTM(128, return_sequences=True)
  - LSTM(64, return_sequences=False)
  - Dense(64, activation='relu')
  - Dropout(0.5)
  - Dense(num_classes, activation='softmax')
- **Output:** Softmax over all sign classes
- **Trained with:** categorical crossentropy, Adam optimizer

---

## Non-Manual Markers (NMMs)

ASL grammar is encoded not just in hands but in facial expressions. Key markers:

- Eyebrow raises — yes/no questions vs wh-questions
- Head tilts and nods
- Mouth morphemes
- Eye gaze direction

Key MediaPipe face landmark indices:
- Eyebrows: 70, 63, 105, 66, 107 (left) / 336, 296, 334, 293, 300 (right)
- Mouth corners: 61, 291
- Nose tip: 4
- Chin: 152

---

## WebSocket API

### Frontend to Backend
    {
      "type": "frame",
      "data": "<base64 encoded jpeg frame>"
    }

### Backend to Frontend
    {
      "type": "translation",
      "sign": "HELLO",
      "confidence": 0.94,
      "sentence": "HELLO HOW ARE YOU"
    }

---

## Key Implementation Notes

1. **No Object Detection API** — do not use tensorflow/models or object_detection. MediaPipe replaces this entirely.
2. **Protobuf** — do not downgrade protobuf. Keep at 4.x for TensorFlow + MediaPipe compatibility.
3. **Venv** — always activate venv before running any Python: `.\venv\Scripts\activate`
4. **Kernel** — if using Jupyter, register venv as a kernel: `python -m ipykernel install --user --name=venv --display-name "Python (venv)"`
5. **Env vars** — set these to suppress TF noise: `TF_CPP_MIN_LOG_LEVEL=3` and `TF_ENABLE_ONEDNN_OPTS=0`
6. **Sign sequencing** — individual signs are buffered into a sentence buffer. A rule-based system or small language model combines them into natural English output.
7. **WLASL** — download videos and WLASL_v0.3.json from the official repo. Place in /data/wlasl/. Run dataset.py to preprocess into landmark sequences before training.

---

## Build Order

1. backend/utils/landmarks.py — MediaPipe Holistic extractor
2. backend/utils/preprocess.py — landmark normalization
3. backend/utils/dataset.py — WLASL loader
4. backend/model/train.py — LSTM training
5. backend/model/predict.py — inference + sliding window
6. backend/main.py — FastAPI WebSocket server
7. frontend/main.js — Electron shell
8. frontend/src/App.jsx — React root
9. frontend/src/components/VideoCall.jsx — WebRTC
10. frontend/src/components/Translator.jsx — translation overlay

---

## Commands

Activate venv:
    .\venv\Scripts\activate

Run backend:
    cd backend
    uvicorn main:app --reload --port 8000

Run frontend (dev):
    cd frontend
    npm run dev

Train model:
    cd backend
    python model/train.py

Test landmark extraction:
    cd backend
    python utils/landmarks.py

---

## Dependencies

### Python (backend/requirements.txt)
    tensorflow==2.15.0
    mediapipe==0.10.14
    opencv-python==4.10.0.84
    fastapi
    uvicorn
    python-socketio
    websockets
    numpy
    scikit-learn

### Node (frontend/package.json)
    electron
    react
    react-dom
    socket.io-client
    vite
    @vitejs/plugin-react
    electron-builder
    concurrently
    wait-on
