import cv2, numpy as np, urllib.request, os, mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "backend/face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

# Landmarks indeices to calculate gaze direction
LEFT_EYE_IDX = 33
RIGHT_EYE_IDX = 263
NOSE_IDX = 1
LEFT_EDGE_IDX = 234
RIGHT_EDGE_IDX = 454

LOOK_AWAY_THRESHOLD = 0.35 # Max desviation accepted

def download_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading FaceLandmarker model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model correctly downloaded.")


class FaceDetector:
    def __init__(self):
        download_model()

        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=True,
            num_faces=1
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

    def analyze(self, frame: np.ndarray) -> dict:
        # Convert frame to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        result = self.landmarker.detect(mp_image)
        if not result.face_landmarks:
            return {
                "face_detected": False,
                "looking_away": False,
                "suspicious": True,
                "detail": "no_face"
            }
        
        landmarks = result.face_landmarks[0]

        # Get coordinates of key points
        nose = landmarks[NOSE_IDX]
        left_edge = landmarks[LEFT_EDGE_IDX]
        right_edge = landmarks[RIGHT_EDGE_IDX]

        # Calculate relative horizontal position of nose
        face_width = right_edge.x - left_edge.x
        if face_width == 0:
            return {
                "face_detected": True,
                "looking_away": False,
                "suspicious": False,
                "detail": "ok"
            }
        nose_relative = (nose.x - left_edge.x)/face_width
        desviation = abs(nose_relative - 0.5)

        # Calculate vertical inclination (pitch) if there is transformation matrix
        looking_away = False
        detail = "ok"
        if result.facial_transformation_matrixes:
            matrix = result.facial_transformation_matrixes[0]
            pitch = matrix[1][2]
            yaw_desviation = desviation

            if yaw_desviation > LOOK_AWAY_THRESHOLD:
                looking_away = True
                detail = "looking_sideways"
            elif pitch < -0.5:
                looking_away = True
                detail = "looking_down"
            elif pitch > 0.5:
                looking_away = True
                detail = "looking_up"
        else:
            if desviation > LOOK_AWAY_THRESHOLD:
                looking_away = True
                detail = "looking_sideways"
        
        return {
            "face_detected": True,
            "looking_away": looking_away,
            "suspicious": looking_away,
            "detail": detail
        }