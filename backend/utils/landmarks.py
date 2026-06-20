import cv2
import mediapipe as mp
import numpy as np

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# 10 key face landmarks: left eyebrow (5) + right eyebrow (5) = 30 values.
# Brows carry much of ASL's grammatical facial expression (questions, topics), so a
# small brow subset gives the model expression signal without the full 468-point mesh.
FACE_KEY_INDICES = [70, 63, 105, 66, 107, 336, 296, 334, 293, 300]

# 12 upper-body pose landmarks: shoulders through hips (indices 11-22) = 36 values.
POSE_UPPER_INDICES = list(range(11, 23))

# Vector layout: left hand (63) + right hand (63) + face (30) + pose (36) = 192.
LANDMARK_DIM = 192


def _vector_from_results(results) -> np.ndarray:
    """Flatten one Holistic result into the fixed 192-value vector.

    Missing components become zeros so the vector is always the same length, which
    the LSTM requires; a dropped hand on a frame must not shift later values.
    """
    lh = (
        np.array([[lm.x, lm.y, lm.z] for lm in results.left_hand_landmarks.landmark]).flatten()
        if results.left_hand_landmarks else np.zeros(63)
    )
    rh = (
        np.array([[lm.x, lm.y, lm.z] for lm in results.right_hand_landmarks.landmark]).flatten()
        if results.right_hand_landmarks else np.zeros(63)
    )
    face = (
        np.array([
            [results.face_landmarks.landmark[i].x,
             results.face_landmarks.landmark[i].y,
             results.face_landmarks.landmark[i].z]
            for i in FACE_KEY_INDICES
        ]).flatten()
        if results.face_landmarks else np.zeros(30)
    )
    pose = (
        np.array([
            [results.pose_landmarks.landmark[i].x,
             results.pose_landmarks.landmark[i].y,
             results.pose_landmarks.landmark[i].z]
            for i in POSE_UPPER_INDICES
        ]).flatten()
        if results.pose_landmarks else np.zeros(36)
    )
    return np.concatenate([lh, rh, face, pose])


def process_frame(frame: np.ndarray, holistic):
    """Run Holistic once and return (192-value vector, raw results).

    The raw results are returned alongside the vector so a caller can draw the
    landmarks without paying for a second inference pass.
    """
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Marking the buffer read-only lets MediaPipe pass it by reference instead of
    # copying, which is a measurable win at camera frame rates.
    rgb.flags.writeable = False
    results = holistic.process(rgb)
    return _vector_from_results(results), results


def extract_landmarks(frame: np.ndarray, holistic) -> np.ndarray:
    """Return only the 192-value landmark vector for one frame.

    Kept as the backend's stable entry point (the WebSocket server calls this); the
    drawing-aware path uses process_frame instead.
    """
    vec, _ = process_frame(frame, holistic)
    return vec


def draw_landmarks(image: np.ndarray, results) -> None:
    """Draw hands, face, and pose onto image in place, for the live detection view.

    Each component is guarded because any of them can be absent on a given frame
    (a hand leaves the frame, the face turns away).
    """
    if results.face_landmarks:
        mp_drawing.draw_landmarks(
            image, results.face_landmarks, mp_holistic.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style(),
        )
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )
    for hand in (results.left_hand_landmarks, results.right_hand_landmarks):
        if hand:
            mp_drawing.draw_landmarks(
                image, hand, mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style(),
            )


def detection_status(results) -> dict:
    """Report which components were detected, for an on-screen readout."""
    return {
        "left_hand": results.left_hand_landmarks is not None,
        "right_hand": results.right_hand_landmarks is not None,
        "face": results.face_landmarks is not None,
        "pose": results.pose_landmarks is not None,
    }
