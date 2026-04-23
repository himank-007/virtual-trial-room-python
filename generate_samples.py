"""
generate_samples.py
-------------------
Creates simple placeholder clothing images for testing.
Run once: python generate_samples.py
"""
import os
import numpy as np
import cv2


def make_shirt(path, color=(70, 130, 200)):
    img = np.ones((400, 300, 4), dtype=np.uint8) * 0
    # Body
    pts = np.array([[50,80],[250,80],[270,350],[30,350]], np.int32)
    cv2.fillPoly(img, [pts], (*color, 255))
    # Left sleeve
    pts = np.array([[50,80],[0,160],[20,180],[60,120]], np.int32)
    cv2.fillPoly(img, [pts], (*color, 255))
    # Right sleeve
    pts = np.array([[250,80],[300,160],[280,180],[240,120]], np.int32)
    cv2.fillPoly(img, [pts], (*color, 255))
    # Collar
    pts = np.array([[120,80],[150,120],[180,80]], np.int32)
    cv2.fillPoly(img, [pts], (255,255,255,255))
    cv2.imwrite(path, img)
    print(f"Created: {path}")


def make_glasses(path, color=(40, 40, 40)):
    img = np.ones((150, 350, 4), dtype=np.uint8) * 0
    # Left lens
    cv2.ellipse(img, (85, 75), (70, 50), 0, 0, 360, (*color, 255), 6)
    # Right lens
    cv2.ellipse(img, (265, 75), (70, 50), 0, 0, 360, (*color, 255), 6)
    # Bridge
    cv2.line(img, (155, 75), (195, 75), (*color, 255), 6)
    # Left arm
    cv2.line(img, (15, 75), (0, 70), (*color, 255), 5)
    # Right arm
    cv2.line(img, (335, 75), (350, 70), (*color, 255), 5)
    cv2.imwrite(path, img)
    print(f"Created: {path}")


def make_hat(path, color=(180, 60, 60)):
    img = np.ones((300, 350, 4), dtype=np.uint8) * 0
    # Brim
    cv2.ellipse(img, (175, 230), (170, 35), 0, 0, 360, (*color, 255), -1)
    # Crown
    pts = np.array([[60,230],[120,60],[230,60],[290,230]], np.int32)
    cv2.fillPoly(img, [pts], (*color, 255))
    # Band
    cv2.line(img, (80, 200), (270, 200), (255,255,255,200), 10)
    cv2.imwrite(path, img)
    print(f"Created: {path}")


def make_outfit(path):
    img = np.ones((500, 300, 4), dtype=np.uint8) * 0
    color_top = (80, 100, 180)
    color_bot = (50, 50, 100)
    # Top
    pts = np.array([[50,50],[250,50],[260,230],[40,230]], np.int32)
    cv2.fillPoly(img, [pts], (*color_top, 255))
    # Collar
    pts = np.array([[120,50],[150,90],[180,50]], np.int32)
    cv2.fillPoly(img, [pts], (255,255,255,255))
    # Pants
    pts = np.array([[40,230],[260,230],[250,480],[160,480],[150,340],[140,480],[50,480]], np.int32)
    cv2.fillPoly(img, [pts], (*color_bot, 255))
    cv2.imwrite(path, img)
    print(f"Created: {path}")


if __name__ == '__main__':
    base = os.path.dirname(__file__)
    cats = {
        "tops": [],
        "accessories_glasses": [],
        "accessories_hats": [],
        "full_outfits": []
    }

    for cat in cats:
        os.makedirs(os.path.join(base, "static", "clothes", cat), exist_ok=True)

    # Shirts
    make_shirt(os.path.join(base, "static/clothes/tops/blue_shirt.png"), (200, 130, 70))
    make_shirt(os.path.join(base, "static/clothes/tops/red_shirt.png"), (60, 60, 200))
    make_shirt(os.path.join(base, "static/clothes/tops/green_shirt.png"), (60, 160, 60))

    # Glasses
    make_glasses(os.path.join(base, "static/clothes/accessories_glasses/black_glasses.png"), (30, 30, 30))
    make_glasses(os.path.join(base, "static/clothes/accessories_glasses/gold_glasses.png"), (30, 180, 210))

    # Hats
    make_hat(os.path.join(base, "static/clothes/accessories_hats/red_cap.png"), (40, 40, 200))
    make_hat(os.path.join(base, "static/clothes/accessories_hats/black_cap.png"), (30, 30, 30))

    # Outfit
    make_outfit(os.path.join(base, "static/clothes/full_outfits/blue_suit.png"))

    print("\n✅ Sample clothing images generated! Run 'python app.py' to start.")
