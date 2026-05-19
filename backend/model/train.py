import os
import json
import numpy as np
from pathlib import Path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

SEQUENCE_DIR = Path(__file__).parents[2] / "data" / "wlasl" / "sequences"
MODEL_DIR = Path(__file__).parent
SEQUENCE_LENGTH = 30
LANDMARK_DIM = 192


def load_dataset() -> tuple[np.ndarray, list]:
    X = np.load(str(SEQUENCE_DIR / "X.npy"))
    with open(str(SEQUENCE_DIR / "y.json")) as f:
        y = json.load(f)
    return X, y


def build_model(num_classes: int) -> tf.keras.Model:
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(SEQUENCE_LENGTH, LANDMARK_DIM)),
        LSTM(64, return_sequences=False),
        Dense(64, activation="relu"),
        Dropout(0.5),
        Dense(num_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def train():
    X, y_raw = load_dataset()

    encoder = LabelEncoder()
    y_encoded = encoder.fit_transform(y_raw)
    num_classes = len(encoder.classes_)
    y_cat = to_categorical(y_encoded, num_classes)

    label_map = {str(i): label for i, label in enumerate(encoder.classes_.tolist())}
    with open(str(MODEL_DIR / "labels.json"), "w") as f:
        json.dump(label_map, f, indent=2)

    X_train, X_val, y_train, y_val = train_test_split(X, y_cat, test_size=0.1, random_state=42)

    model = build_model(num_classes)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(str(MODEL_DIR / "model.keras"), save_best_only=True),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=100,
        batch_size=32,
        callbacks=callbacks,
    )
    print(f"\nDone. {num_classes} classes. Model saved to {MODEL_DIR / 'model.keras'}")


if __name__ == "__main__":
    train()
