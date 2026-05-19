import numpy as np

SEQUENCE_LENGTH = 30
LANDMARK_DIM = 192


def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
    """Scale landmarks to [0, 1] range per frame. Returns zeros if all values are identical."""
    lo, hi = landmarks.min(), landmarks.max()
    if hi == lo:
        return np.zeros_like(landmarks)
    return (landmarks - lo) / (hi - lo)


def pad_or_trim(sequence: list, length: int = SEQUENCE_LENGTH) -> np.ndarray:
    """Ensure a landmark sequence is exactly `length` frames by zero-padding or truncating."""
    seq = np.array(sequence)
    if len(seq) < length:
        pad = np.zeros((length - len(seq), LANDMARK_DIM))
        seq = np.vstack([pad, seq])
    else:
        seq = seq[-length:]
    return seq


def build_input(sequence: list) -> np.ndarray:
    """Return a (1, 30, 192) tensor ready for model inference."""
    seq = pad_or_trim(sequence)
    seq = np.array([normalize_landmarks(frame) for frame in seq])
    return np.expand_dims(seq, axis=0)
