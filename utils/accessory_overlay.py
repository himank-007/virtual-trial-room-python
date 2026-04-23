import cv2
import numpy as np


class AccessoryOverlay:
    """
    Overlays accessories (glasses, hats) onto a person image
    using face and pose keypoints from PoseEstimator.
    """

    def apply_glasses(self, base_img, glasses_img, keypoints):
        """
        Place glasses over the eye region.
        Uses left_eye, right_eye keypoints or face_bbox as fallback.
        """
        le = keypoints.get("left_eye")
        re = keypoints.get("right_eye")
        face_bbox = keypoints.get("face_bbox")

        if le and re:
            eye_center_x = (le[0] + re[0]) // 2
            eye_center_y = (le[1] + re[1]) // 2
            eye_width = int(abs(re[0] - le[0]) * 2.2)  # glasses wider than eye span
            eye_height = int(eye_width * 0.45)

            x1 = eye_center_x - eye_width // 2
            y1 = eye_center_y - eye_height // 2
        elif face_bbox:
            fx, fy, fw, fh = face_bbox
            eye_width = int(fw * 1.1)
            eye_height = int(fw * 0.35)
            x1 = fx + fw // 2 - eye_width // 2
            y1 = fy + int(fh * 0.35)
        else:
            return base_img  # No face detected

        return self._blend_accessory(base_img, glasses_img, x1, y1, eye_width, eye_height)

    def apply_hat(self, base_img, hat_img, keypoints):
        """
        Place a hat above the head.
        Uses nose + shoulder width to determine placement and scale.
        """
        nose = keypoints.get("nose")
        face_bbox = keypoints.get("face_bbox")
        ls = keypoints.get("left_shoulder")
        rs = keypoints.get("right_shoulder")

        if face_bbox:
            fx, fy, fw, fh = face_bbox
            hat_w = int(fw * 1.6)
            hat_h = int(hat_w * self._hat_aspect(hat_img))
            x1 = fx + fw // 2 - hat_w // 2
            y1 = fy - int(hat_h * 0.85)
        elif nose and ls and rs:
            face_width = int(abs(rs[0] - ls[0]) * 0.7)
            hat_w = int(face_width * 1.4)
            hat_h = int(hat_w * self._hat_aspect(hat_img))
            x1 = nose[0] - hat_w // 2
            y1 = nose[1] - int(hat_h * 1.2)
        else:
            return base_img

        return self._blend_accessory(base_img, hat_img, x1, y1, hat_w, hat_h)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _blend_accessory(self, base_img, acc_img, x1, y1, target_w, target_h):
        """Resize accessory image and alpha-blend onto base."""
        h_img, w_img = base_img.shape[:2]

        acc_rgba = self._ensure_rgba(acc_img)
        resized = cv2.resize(acc_rgba, (max(target_w, 1), max(target_h, 1)),
                             interpolation=cv2.INTER_AREA)

        # Clip to image boundaries
        x1c, y1c = max(x1, 0), max(y1, 0)
        x2c = min(x1 + target_w, w_img)
        y2c = min(y1 + target_h, h_img)

        rx1 = x1c - x1
        ry1 = y1c - y1
        rx2 = rx1 + (x2c - x1c)
        ry2 = ry1 + (y2c - y1c)

        if rx2 <= rx1 or ry2 <= ry1:
            return base_img

        acc_crop = resized[ry1:ry2, rx1:rx2]
        base_crop = base_img[y1c:y2c, x1c:x2c]

        if acc_crop.shape[:2] != base_crop.shape[:2]:
            return base_img

        alpha = acc_crop[:, :, 3:4].astype(np.float32) / 255.0
        acc_bgr = acc_crop[:, :, :3].astype(np.float32)
        base_bgr = base_crop.astype(np.float32)

        blended = (acc_bgr * alpha + base_bgr * (1 - alpha)).astype(np.uint8)
        base_img[y1c:y2c, x1c:x2c] = blended
        return base_img

    @staticmethod
    def _hat_aspect(hat_img):
        """Return height/width aspect ratio of hat image."""
        h, w = hat_img.shape[:2]
        return h / max(w, 1)

    @staticmethod
    def _ensure_rgba(img):
        """Convert BGR or BGRA image to BGRA with smart alpha."""
        if img.shape[2] == 4:
            return img
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = mask
        return bgra
