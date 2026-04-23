import cv2
import numpy as np
import mediapipe as mp


class PoseEstimator:
    """
    Detects human body pose landmarks using MediaPipe Pose.
    Returns a dictionary of key body points used for clothing overlay.
    """

    # MediaPipe landmark indices
    LANDMARKS = {
        "nose": 0,
        "left_eye": 2,
        "right_eye": 5,
        "left_ear": 7,
        "right_ear": 8,
        "left_shoulder": 11,
        "right_shoulder": 12,
        "left_elbow": 13,
        "right_elbow": 14,
        "left_wrist": 15,
        "right_wrist": 16,
        "left_hip": 23,
        "right_hip": 24,
        "left_knee": 25,
        "right_knee": 26,
        "left_ankle": 27,
        "right_ankle": 28,
    }

    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_face = mp.solutions.face_detection
        self.mp_draw = mp.solutions.drawing_utils

        self.pose = self.mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.5,
        )
        self.face_detector = self.mp_face.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )

    def detect(self, img_bgr):
        """
        Detect pose keypoints from a BGR image.

        Returns:
            dict with keys from LANDMARKS + 'face_bbox' | None if not detected
        """
        h, w = img_bgr.shape[:2]
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        result = self.pose.process(img_rgb)
        if not result.pose_landmarks:
            return None

        lm = result.pose_landmarks.landmark
        keypoints = {}

        for name, idx in self.LANDMARKS.items():
            pt = lm[idx]
            # Visibility threshold
            if pt.visibility < 0.3:
                keypoints[name] = None
            else:
                keypoints[name] = (int(pt.x * w), int(pt.y * h))

        # Add face bounding box via face detection
        keypoints["face_bbox"] = self._detect_face(img_rgb, h, w)

        # Compute derived midpoints
        keypoints["mid_shoulder"] = self._midpoint(
            keypoints.get("left_shoulder"), keypoints.get("right_shoulder")
        )
        keypoints["mid_hip"] = self._midpoint(
            keypoints.get("left_hip"), keypoints.get("right_hip")
        )
        keypoints["neck"] = self._neck_point(
            keypoints.get("mid_shoulder"), keypoints.get("nose")
        )

        return keypoints

    def _detect_face(self, img_rgb, h, w):
        """Returns (x, y, width, height) of the first detected face, or None."""
        result = self.face_detector.process(img_rgb)
        if not result.detections:
            return None
        det = result.detections[0]
        bbox = det.location_data.relative_bounding_box
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        fw = int(bbox.width * w)
        fh = int(bbox.height * h)
        return (x, y, fw, fh)

    @staticmethod
    def _midpoint(a, b):
        if a is None or b is None:
            return None
        return ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)

    @staticmethod
    def _neck_point(mid_shoulder, nose):
        if mid_shoulder is None or nose is None:
            return mid_shoulder
        # Neck is ~70% from nose to mid_shoulder
        nx = int(nose[0] * 0.3 + mid_shoulder[0] * 0.7)
        ny = int(nose[1] * 0.3 + mid_shoulder[1] * 0.7)
        return (nx, ny)

    def draw_keypoints(self, img_bgr, keypoints):
        """Draw keypoints on image for debugging."""
        for name, pt in keypoints.items():
            if pt is None or name == "face_bbox":
                continue
            cv2.circle(img_bgr, pt, 5, (0, 255, 0), -1)
            cv2.putText(
                img_bgr, name[:4], (pt[0] + 5, pt[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 0), 1
            )
        if keypoints.get("face_bbox"):
            x, y, fw, fh = keypoints["face_bbox"]
            cv2.rectangle(img_bgr, (x, y), (x + fw, y + fh), (0, 0, 255), 2)
        return img_bgr
