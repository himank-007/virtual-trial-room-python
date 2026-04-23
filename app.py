from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import json

from utils.pose_estimator import PoseEstimator
from utils.cloth_overlay import ClothOverlay
from utils.accessory_overlay import AccessoryOverlay

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['CLOTHES_FOLDER'] = 'static/clothes'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

pose_estimator = PoseEstimator()
cloth_overlay = ClothOverlay()
accessory_overlay = AccessoryOverlay()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def decode_base64_image(data_url):
    """Decode base64 image from data URL."""
    header, data = data_url.split(',', 1)
    img_bytes = base64.b64decode(data)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return img

def encode_image_to_base64(img):
    """Encode OpenCV image to base64 string."""
    _, buffer = cv2.imencode('.png', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"

@app.route('/')
def index():
    clothes = get_clothes_catalog()
    return render_template('index.html', clothes=clothes)

@app.route('/api/catalog')
def get_catalog():
    return jsonify(get_clothes_catalog())

def get_clothes_catalog():
    catalog = {
        "tops": [],
        "accessories_glasses": [],
        "accessories_hats": [],
        "full_outfits": []
    }
    clothes_dir = app.config['CLOTHES_FOLDER']
    if os.path.exists(clothes_dir):
        for category in catalog:
            cat_dir = os.path.join(clothes_dir, category)
            if os.path.exists(cat_dir):
                for f in os.listdir(cat_dir):
                    if allowed_file(f):
                        catalog[category].append({
                            "name": f.rsplit('.', 1)[0].replace('_', ' ').title(),
                            "path": f"/static/clothes/{category}/{f}",
                            "filename": f,
                            "category": category
                        })
    return catalog

@app.route('/api/try-on', methods=['POST'])
def try_on():
    """Main endpoint to apply virtual try-on."""
    data = request.get_json()
    
    if not data or 'user_image' not in data or 'clothing_path' not in data:
        return jsonify({"error": "Missing user_image or clothing_path"}), 400

    try:
        user_img = decode_base64_image(data['user_image'])
        category = data.get('category', 'tops')
        clothing_path = data['clothing_path'].lstrip('/')

        # Load clothing image
        cloth_img = cv2.imread(clothing_path, cv2.IMREAD_UNCHANGED)
        if cloth_img is None:
            return jsonify({"error": "Could not load clothing image"}), 400

        # Detect pose keypoints
        keypoints = pose_estimator.detect(user_img)
        if keypoints is None:
            return jsonify({"error": "No person detected. Please use a clear, well-lit photo."}), 400

        # Apply overlay based on category
        if category == 'tops':
            result = cloth_overlay.apply_top(user_img.copy(), cloth_img, keypoints)
        elif category == 'full_outfits':
            result = cloth_overlay.apply_full_outfit(user_img.copy(), cloth_img, keypoints)
        elif category == 'accessories_glasses':
            result = accessory_overlay.apply_glasses(user_img.copy(), cloth_img, keypoints)
        elif category == 'accessories_hats':
            result = accessory_overlay.apply_hat(user_img.copy(), cloth_img, keypoints)
        else:
            result = cloth_overlay.apply_top(user_img.copy(), cloth_img, keypoints)

        result_b64 = encode_image_to_base64(result)
        return jsonify({"result_image": result_b64, "success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload-clothing', methods=['POST'])
def upload_clothing():
    """Allow users to upload their own clothing items."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    category = request.form.get('category', 'tops')

    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({"error": "Invalid file"}), 400

    save_dir = os.path.join(app.config['CLOTHES_FOLDER'], category)
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, file.filename)
    file.save(filepath)

    return jsonify({
        "success": True,
        "path": f"/static/clothes/{category}/{file.filename}",
        "name": file.filename.rsplit('.', 1)[0].replace('_', ' ').title()
    })

@app.route('/api/keypoints', methods=['POST'])
def get_keypoints():
    """Debug endpoint to visualize detected keypoints."""
    data = request.get_json()
    if not data or 'user_image' not in data:
        return jsonify({"error": "Missing user_image"}), 400

    user_img = decode_base64_image(data['user_image'])
    keypoints = pose_estimator.detect(user_img)

    if keypoints is None:
        return jsonify({"detected": False})

    debug_img = pose_estimator.draw_keypoints(user_img.copy(), keypoints)
    return jsonify({
        "detected": True,
        "debug_image": encode_image_to_base64(debug_img),
        "keypoints": keypoints
    })

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['CLOTHES_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
