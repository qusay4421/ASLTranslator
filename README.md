# ASLTranslator

Real-time American Sign Language translation. A webcam feed is run through MediaPipe
Holistic to extract hand, face, and pose landmarks, an LSTM classifies the landmark
sequence into a sign, and the translated text is shown on screen. The longer-term goal
is an overlay inside a video call; see `CLAUDE.md` for the full spec.

## Quick start (detection app)

Requires Python 3.10 to 3.12 (MediaPipe's legacy Holistic solution is not in the
3.13+ wheels).

```sh
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python app.py                 # webcam with hands, face, and pose drawn live
python app.py --translate     # also overlay sign predictions from the trained model
```

Keys: `q` quits, `c` clears the translated sentence.

## Add your own signs

```sh
cd backend
python collect.py --label hello --takes 30   # record sequences from the webcam
python collect.py --label thanks --takes 30
python model/train.py                        # retrain on the updated dataset
```

## Layout

```
backend/
  app.py               standalone real-time detection and translation app
  collect.py           webcam data collection for new signs
  main.py              FastAPI WebSocket server (used by the Electron app)
  utils/landmarks.py   Holistic landmark extraction and drawing
  utils/preprocess.py  normalize and shape landmark sequences for the model
  model/train.py       LSTM training
  model/predict.py     sliding-window inference
  tests/               pure-numpy preprocessing tests
frontend/              Electron + React + WebRTC video-call app
```

## Tests

```sh
cd backend
python tests/test_preprocess.py    # or: python -m pytest tests/
```

Progress is tracked in `DEVLOG.md` (newest entry on top).
