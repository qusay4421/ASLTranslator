import cv2
import mediapipe as mp
import numpy as np

mp_holistic = mp.solutions.holistic

# 10 key face landmarks: left eyebrow (5) + right eyebrow (5) = 30 values
FACE_KEY_INDICES = [70, 63, 105, 66, 107, 336, 296, 334, 293, 300]

# 12 upper-body pose landmarks: shoulders through hips (indices 11-22) = 36 values
POSE_UPPER_INDICES = list(range(11, 23))


def extract_landmarks(frame: np.ndarray, holistic) -> np.ndarray:
    """Return a 192-value landmark vector for one frame."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = holistic.process(rgb)

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

    return np.concatenate([lh, rh, face, pose])  # 192 values


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            landmarks = extract_landmarks(frame, holistic)
            print(f"Landmark vector shape: {landmarks.shape}")
            cv2.imshow("Landmark Test", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    cap.release()
    cv2.destroyAllWindows()
