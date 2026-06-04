"""Unit tests for the pure landmark preprocessing pipeline.

These cover utils.preprocess, which is free of heavy ML deps (only numpy),
so they run fast and deterministically. They lock in the tensor shapes and
normalization contract that model/predict.py relies on.
"""
import numpy as np
import pytest

from utils.preprocess import (
    SEQUENCE_LENGTH,
    LANDMARK_DIM,
    normalize_landmarks,
    pad_or_trim,
    build_input,
)


# --- normalize_landmarks -------------------------------------------------

def test_normalize_scales_to_unit_range():
    arr = np.array([0.0, 5.0, 10.0])
    out = normalize_landmarks(arr)
    np.testing.assert_allclose(out, [0.0, 0.5, 1.0])


def test_normalize_min_and_max_are_zero_and_one():
    arr = np.array([-3.0, 2.0, 7.0, 11.0])
    out = normalize_landmarks(arr)
    assert out.min() == pytest.approx(0.0)
    assert out.max() == pytest.approx(1.0)


def test_normalize_constant_frame_returns_zeros():
    # When every value is identical there is no range to scale into,
    # so the function must return zeros rather than divide by zero.
    arr = np.full(LANDMARK_DIM, 5.0)
    out = normalize_landmarks(arr)
    assert np.all(out == 0.0)
    assert out.shape == arr.shape


def test_normalize_preserves_shape():
    arr = np.random.rand(LANDMARK_DIM)
    assert normalize_landmarks(arr).shape == (LANDMARK_DIM,)


# --- pad_or_trim ---------------------------------------------------------

def test_pad_short_sequence_front_pads_with_zeros():
    frames = [np.full(LANDMARK_DIM, 1.0) for _ in range(5)]
    out = pad_or_trim(frames)
    assert out.shape == (SEQUENCE_LENGTH, LANDMARK_DIM)
    # Padding is prepended, so the leading rows are zero...
    assert np.all(out[: SEQUENCE_LENGTH - 5] == 0.0)
    # ...and the original frames sit at the tail, in order.
    assert np.all(out[SEQUENCE_LENGTH - 5:] == 1.0)


def test_exact_length_sequence_unchanged():
    frames = [np.full(LANDMARK_DIM, float(i)) for i in range(SEQUENCE_LENGTH)]
    out = pad_or_trim(frames)
    assert out.shape == (SEQUENCE_LENGTH, LANDMARK_DIM)
    np.testing.assert_array_equal(out, np.array(frames))


def test_long_sequence_keeps_most_recent_frames():
    extra = 10
    frames = [np.full(LANDMARK_DIM, float(i)) for i in range(SEQUENCE_LENGTH + extra)]
    out = pad_or_trim(frames)
    assert out.shape == (SEQUENCE_LENGTH, LANDMARK_DIM)
    # The oldest `extra` frames are dropped; first kept row is frame `extra`.
    assert out[0, 0] == pytest.approx(float(extra))
    assert out[-1, 0] == pytest.approx(float(SEQUENCE_LENGTH + extra - 1))


def test_pad_or_trim_returns_ndarray():
    out = pad_or_trim([np.zeros(LANDMARK_DIM)])
    assert isinstance(out, np.ndarray)


# --- build_input ---------------------------------------------------------

def test_build_input_shape_is_batch_ready():
    frames = [np.random.rand(LANDMARK_DIM) for _ in range(SEQUENCE_LENGTH)]
    out = build_input(frames)
    assert out.shape == (1, SEQUENCE_LENGTH, LANDMARK_DIM)


def test_build_input_pads_short_sequence():
    frames = [np.random.rand(LANDMARK_DIM) for _ in range(3)]
    out = build_input(frames)
    assert out.shape == (1, SEQUENCE_LENGTH, LANDMARK_DIM)


def test_build_input_values_are_normalized_or_zero():
    frames = [np.random.rand(LANDMARK_DIM) * 100 for _ in range(SEQUENCE_LENGTH)]
    out = build_input(frames)[0]
    # Every frame is either an all-zero pad row or scaled into [0, 1].
    for frame in out:
        assert frame.min() >= -1e-9
        assert frame.max() <= 1.0 + 1e-9
