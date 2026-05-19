import os
import json
import numpy as np
from pathlib import Path
from collections import deque

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
from utils.preprocess import build_input

MODEL_DIR = Path(__file__).parent
SEQUENCE_LENGTH = 30
CONFIDENCE_THRESHOLD = 0.7
SENTENCE_MAX = 10


class SignPredictor:
    def __init__(self):
        self.model = tf.keras.models.load_model(str(MODEL_DIR / "model.keras"))
        with open(str(MODEL_DIR / "labels.json")) as f:
            self.labels = json.load(f)
        self.frame_buffer: deque = deque(maxlen=SEQUENCE_LENGTH)
        self.sentence: deque = deque(maxlen=SENTENCE_MAX)
        self.last_sign: str | None = None

    def add_frame(self, landmarks: np.ndarray) -> None:
        self.frame_buffer.append(landmarks)

    def predict(self) -> dict | None:
        """Return prediction dict or None if buffer not full / confidence too low."""
        if len(self.frame_buffer) < SEQUENCE_LENGTH:
            return None

        probs = self.model.predict(build_input(list(self.frame_buffer)), verbose=0)[0]
        idx = int(np.argmax(probs))
        confidence = float(probs[idx])

        if confidence < CONFIDENCE_THRESHOLD:
            return None

        sign = self.labels[str(idx)]
        if sign != self.last_sign:
            self.last_sign = sign
            self.sentence.append(sign)

        return {
            "sign": sign,
            "confidence": confidence,
            "sentence": " ".join(self.sentence),
        }
