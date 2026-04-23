import cv2
import numpy as np


class ClothOverlay:
    """
    Overlays clothing images (tops / full outfits) onto a person image
    using pose keypoints from PoseEstimator.
    """

    def apply_top(self, base_img, cloth_img, keypoints):
        """
        Warp and blend a top/shirt onto the person.
        The cloth is scaled to span from shoulder to hip.
        """
        ls = keypoints.get("left_shoulder")
        rs = keypoints.get("right_shoulder")
        lh = keypoints.get("left_hip")
        rh = keypoints.get("right_hip")

        if not all([ls, rs, lh, rh]):
            return base_img  # Can't place without these points

        # ---- Target region on the person ----
        shoulder_width = abs(rs[0] - ls[0])
        torso_height = abs(lh[1] - ls[1])

        # Add padding so cloth covers sides naturally
        pad_w = int(shoulder_width * 0.35)
        pad_h_top = int(torso_height * 0.05)
        pad_h_bot = int(torso_height * 0.15)

        # Top-left corner of clothing region
        x1 = min(ls[0], rs[0]) - pad_w
        y1 = min(ls[1], rs[1]) - pad_h_top
        x2 = max(ls[0], rs[0]) + pad_w
        y2 = max(lh[1], rh[1]) + pad_h_bot

        target_w = max(x2 - x1, 1)
        target_h = max(y2 - y1, 1)

        return self._blend_cloth(base_img, cloth_img, x1, y1, target_w, target_h)

    def apply_full_outfit(self, base_img, cloth_img, keypoints):
        """
        Warp a full outfit from shoulders down to ankles.
        """
        ls = keypoints.get("left_shoulder")
        rs = keypoints.get("right_shoulder")
        la = keypoints.get("left_ankle")
        ra = keypoints.get("right_ankle")
        lh = keypoints.get("left_hip")
        rh = keypoints.get("right_hip")

        # Fall back to hip if ankles not visible
        bottom_left = la if la else lh
        bottom_right = ra if ra else rh

        if not all([ls, rs, bottom_left, bottom_right]):
            return base_img

        shoulder_width = abs(rs[0] - ls[0])
        pad_w = int(shoulder_width * 0.4)
        pad_h_top = int(shoulder_width * 0.05)

        x1 = min(ls[0], rs[0]) - pad_w
        y1 = min(ls[1], rs[1]) - pad_h_top
        x2 = max(ls[0], rs[0]) + pad_w
        y2 = max(bottom_left[1], bottom_right[1]) + 10

        target_w = max(x2 - x1, 1)
        target_h = max(y2 - y1, 1)

        return self._blend_cloth(base_img, cloth_img, x1, y1, target_w, target_h)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _blend_cloth(self, base_img, cloth_img, x1, y1, target_w, target_h):
        """Resize cloth, extract alpha mask, and alpha-composite onto base."""
        h_img, w_img = base_img.shape[:2]

        # Ensure cloth has alpha channel
        cloth_rgba = self._ensure_rgba(cloth_img)

        # Resize cloth to target dimensions
        resized = cv2.resize(cloth_rgba, (target_w, target_h), interpolation=cv2.INTER_AREA)

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

        cloth_crop = resized[ry1:ry2, rx1:rx2]
        base_crop = base_img[y1c:y2c, x1c:x2c]

        if cloth_crop.shape[:2] != base_crop.shape[:2]:
            return base_img

        alpha = cloth_crop[:, :, 3:4].astype(np.float32) / 255.0
        cloth_bgr = cloth_crop[:, :, :3].astype(np.float32)
        base_bgr = base_crop.astype(np.float32)

        blended = (cloth_bgr * alpha + base_bgr * (1 - alpha)).astype(np.uint8)
        base_img[y1c:y2c, x1c:x2c] = blended
        return base_img

    @staticmethod
    def _ensure_rgba(img):
        """Convert BGR or BGRA image to BGRA."""
        if img.shape[2] == 4:
            return img
        # Create alpha from white background removal
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        alpha = mask
        bgra = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        bgra[:, :, 3] = alpha
        return bgra
