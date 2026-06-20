"""Tests for the pure-numpy preprocessing logic.

These have no MediaPipe or TensorFlow dependency, so they run anywhere numpy is
installed and guard the array-shaping that the model's input contract depends on.

Run from the backend/ directory:
    python -m pytest tests/            # if pytest is available
    python tests/test_preprocess.py    # standalone, no pytest needed
"""

import os
import sys

import numpy as np

# Allow running as a plain script from backend/ without installing the package.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.preprocess import (  # noqa: E402
    normalize_landmarks,
    pad_or_trim,
    build_input,
    SEQUENCE_LENGTH,
    LANDMARK_DIM,
)


def test_normalize_scales_to_unit_range():
    out = normalize_landmarks(np.array([0.0, 5.0, 10.0]))
    assert out.min() == 0.0 and out.max() == 1.0
    assert np.allclose(out, [0.0, 0.5, 1.0])


def test_normalize_identical_values_returns_zeros():
    # A frame where every value is equal has no range; dividing by (hi-lo) would be a
    # divide-by-zero, so it must collapse to zeros instead.
    out = normalize_landmarks(np.full(8, 0.42))
    assert np.all(out == 0.0)


def test_pad_or_trim_pads_short_at_front():
    seq = [np.ones(LANDMARK_DIM) for _ in range(5)]
    out = pad_or_trim(seq, SEQUENCE_LENGTH)
    assert out.shape == (SEQUENCE_LENGTH, LANDMARK_DIM)
    # Padding goes at the front, so the real (recent) frames stay at the end where the
    # sliding-window classifier expects the latest motion.
    assert np.all(out[0] == 0.0)
    assert np.all(out[-1] == 1.0)


def test_pad_or_trim_keeps_last_frames_when_long():
    seq = [np.full(LANDMARK_DIM, i, dtype=float) for i in range(SEQUENCE_LENGTH + 10)]
    out = pad_or_trim(seq, SEQUENCE_LENGTH)
    assert out.shape == (SEQUENCE_LENGTH, LANDMARK_DIM)
    # The most recent SEQUENCE_LENGTH frames are kept; the oldest 10 are dropped.
    assert out[-1][0] == SEQUENCE_LENGTH + 9
    assert out[0][0] == 10


def test_build_input_shape_is_model_ready():
    seq = [np.random.rand(LANDMARK_DIM) for _ in range(SEQUENCE_LENGTH)]
    out = build_input(seq)
    assert out.shape == (1, SEQUENCE_LENGTH, LANDMARK_DIM)


def test_build_input_pads_partial_sequence():
    out = build_input([np.random.rand(LANDMARK_DIM) for _ in range(3)])
    assert out.shape == (1, SEQUENCE_LENGTH, LANDMARK_DIM)


def _run_standalone():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL {t.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_standalone() else 0)
