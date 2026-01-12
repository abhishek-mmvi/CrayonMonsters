import sys
import os
import base64
import io
import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps
from flask import Flask, render_template, request, jsonify

# Add parent directories to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add StatGen to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'StatGen')))

try:
    from llm_client import generate_creature_stats
    from stat_engine import validate_creature
    STATGEN_AVAILABLE = True
    print("StatGen modules loaded.")
except ImportError as e:
    print(f"StatGen not available: {e}")
    STATGEN_AVAILABLE = False

app = Flask(__name__)

# Load Model & Labels globally
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'doodle_model.h5')
LABEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'label_map.npy')

print(f"Loading model from {MODEL_PATH}...")
model = tf.keras.models.load_model(MODEL_PATH)
label_map = np.load(LABEL_PATH, allow_pickle=True).item()
print("Model loaded.")

def smart_preprocess(image_bytes):
    """
    Robust preprocessing pipeline.
    Expects bytes (PNG) from canvas.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        # Handle transparency (Canvas usually sends transparent BG)
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("L")
        
        # Invert: Canvas (Black on White) -> Model (White on Black)
        img = ImageOps.invert(img)
        
        # Auto-Crop
        bbox = img.getbbox()
        if bbox:
            left, upper, right, lower = bbox
            width, height = right - left, lower - upper
            pad = max(width, height) * 0.1
            cx, cy = (left + right) / 2, (upper + lower) / 2
            size = max(width, height) + pad * 2
            
            box = (
                int(cx - size / 2),
                int(cy - size / 2),
                int(cx + size / 2),
                int(cy + size / 2)
            )
            img = img.crop(box)
        
        # Resize
        img = img.resize((28, 28), Image.Resampling.LANCZOS)
        
        # Normalize & Auto-Contrast
        arr = np.array(img).astype("float32") / 255.0
        
        min_val = arr.min()
        max_val = arr.max()
        if max_val - min_val > 0.0:
            arr = (arr - min_val) / (max_val - min_val)
        else:
            arr = np.zeros_like(arr)
            
        arr[arr < 0.2] = 0.0
        
        return arr.reshape(1, 28, 28, 1)
        
    except Exception as e:
        print(f"Preprocessing error: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get base64 image from JSON
        data = request.json['image']
        # Remove header like "data:image/png;base64,"
        if "base64," in data:
            data = data.split("base64,")[1]
            
        image_bytes = base64.b64decode(data)
        
        input_tensor = smart_preprocess(image_bytes)
        
        if input_tensor is None:
            return jsonify({'error': 'Failed to process image'}), 400
            
        preds = model.predict(input_tensor, verbose=0)[0]
        
        # Get Top 3
        top_indices = preds.argsort()[-3:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'label': label_map[idx],
                'confidence': float(preds[idx])
            })
            
        return jsonify({'predictions': results})
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/predict_with_stats', methods=['POST'])
def predict_with_stats():
    """
    Combined endpoint: Predict creature type AND generate stats.
    """
    try:
        # Get base64 image from JSON
        data = request.json['image']
        if "base64," in data:
            data = data.split("base64,")[1]
            
        image_bytes = base64.b64decode(data)
        input_tensor = smart_preprocess(image_bytes)
        
        if input_tensor is None:
            return jsonify({'error': 'Failed to process image'}), 400
            
        preds = model.predict(input_tensor, verbose=0)[0]
        
        # Get top prediction
        top_idx = preds.argmax()
        top_label = label_map[top_idx]
        top_confidence = float(preds[top_idx])
        
        # Generate stats if StatGen is available
        if STATGEN_AVAILABLE:
            raw_creature = generate_creature_stats(top_label, top_confidence)
            if "error" not in raw_creature:
                validated_creature, warnings = validate_creature(raw_creature)
                return jsonify({
                    'prediction': {
                        'label': top_label,
                        'confidence': top_confidence
                    },
                    'creature': validated_creature,
                    'warnings': warnings
                })
            else:
                return jsonify({
                    'prediction': {'label': top_label, 'confidence': top_confidence},
                    'error': f"StatGen error: {raw_creature['error']}"
                }), 500
        else:
            return jsonify({
                'prediction': {'label': top_label, 'confidence': top_confidence},
                'creature': None,
                'message': 'StatGen not available'
            })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import webbrowser
    from threading import Timer

    def open_browser():
        webbrowser.open("http://127.0.0.1:5000")

    # Wait 1.5 seconds for server to start, then open browser
    Timer(1.5, open_browser).start()
    
    # Debug=False is important here! 
    # Debug=True creates a reloader that loads the model TWICE, taking 2x time.
    app.run(debug=False, port=5000)
