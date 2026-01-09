import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps

# Load Model & Labels
model = tf.keras.models.load_model("doodle_model.h5")
label_map = np.load("label_map.npy", allow_pickle=True).item()

def smart_preprocess(image_path):
    """
    Robust preprocessing for user-drawn images:
    1. Handle Alpha / White background.
    2. Invert to White-on-Black (which the model expects).
    3. Auto-Crop to remove empty space.
    4. Resize to 28x28.
    5. Auto-Contrast / Normalize to recover thin/faint lines.
    """
    # 1. Load and composite on White (handle transparency)
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img).convert("L")
    
    # 2. Invert (Black strokes -> White strokes on Black background)
    img = ImageOps.invert(img)
    
    # 3. Auto-Crop (Find the drawing)
    bbox = img.getbbox()
    if bbox:
        left, upper, right, lower = bbox
        width, height = right - left, lower - upper
        
        # Add padding (10%)
        pad = max(width, height) * 0.1
        
        # Center in square
        cx, cy = (left + right) / 2, (upper + lower) / 2
        size = max(width, height) + pad * 2
        
        box = (
            int(cx - size / 2),
            int(cy - size / 2),
            int(cx + size / 2),
            int(cy + size / 2)
        )
        img = img.crop(box)
    
    # 4. Resize to 28x28
    img = img.resize((28, 28), Image.Resampling.LANCZOS)
    
    # 5. Normalize & Auto-Contrast
    arr = np.array(img).astype("float32") / 255.0
    
    # Stretch contrast: Map min..max to 0..1
    # This recovers faint lines caused by downscaling.
    min_val = arr.min()
    max_val = arr.max()
    if max_val - min_val > 0.0:
        arr = (arr - min_val) / (max_val - min_val)
    else:
        arr = np.zeros_like(arr)
        
    # Clean noise (hard zero for background)
    arr[arr < 0.2] = 0.0
    
    return arr.reshape(1, 28, 28, 1)

# Run Inference
input_tensor = smart_preprocess("pixels.png") # Changed from my_drawing.png for testing

if input_tensor is not None:
    preds = model.predict(input_tensor, verbose=0)[0]
    
    # Get Top 3
    top_indices = preds.argsort()[-3:][::-1]
    
    print("\n--- Predictions ---")
    for idx in top_indices:
        print(f"{label_map[idx]}: {preds[idx]*100:.2f}%")
        
    best_idx = top_indices[0]
    print(f"\nFinal Result: {label_map[best_idx]}")
