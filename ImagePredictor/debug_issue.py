import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps, ImageChops, ImageFilter

model = tf.keras.models.load_model("doodle_model.h5")
label_map = np.load("label_map.npy", allow_pickle=True).item()

print("\n--- Smart Preprocessing Test (With Dilation) ---")

def smart_process(image_path):
    # 1. Load and handle Alpha
    img = Image.open(image_path).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img).convert("L")
    
    # 2. Invert (Black strokes -> White strokes on Black background)
    img = ImageOps.invert(img)
    
    # 3. Auto-Crop
    bbox = img.getbbox()
    if bbox:
        left, upper, right, lower = bbox
        width, height = right - left, lower - upper
        print(f"DEBUG: Found content bbox: {width}x{height} at ({left}, {upper})")
        
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
    else:
        print("DEBUG: No content found!")
    
    # 3.5 DILATE REMOVED - Using Auto-Contrast instead
    
    # 4. Resize to 28x28
    img = img.resize((28, 28), Image.Resampling.LANCZOS)
    
    # 5. Normalize & Auto-Contrast
    arr = np.array(img).astype("float32") / 255.0
    
    # Auto-Contrast: Stretch the pixel values so the max becomes 1.0 (White)
    # and min becomes 0.0 (Black).
    # Since we are inverted, the background is near 0.0, lines are > 0.
    
    min_val = arr.min()
    max_val = arr.max()
    
    if max_val - min_val > 0.0:
        arr = (arr - min_val) / (max_val - min_val)
    else:
        # Image is flat color?
        arr = np.zeros_like(arr)
        
    # Optional: Clean up noise (background now exactly 0)
    # The resizing might typically result in "ringing" or noise.
    # Let's simple-threshold low values to keep background black.
    arr[arr < 0.2] = 0.0
    
    return arr

try:
    arr = smart_process("untitled.png")
    
    # Save debug view
    Image.fromarray((arr * 255).astype(np.uint8)).save("debug_smart_view.png")
    print("Saved 'debug_smart_view.png' - Check this!")
    
    # Predict
    input_tensor = arr.reshape(1, 28, 28, 1)
    preds = model.predict(input_tensor, verbose=0)[0]
    
    # Top 5
    top_indices = preds.argsort()[-5:][::-1]
    
    print("\nTop 5 Predictions (Smart Process):")
    for idx in top_indices:
        print(f"{label_map[idx]}: {preds[idx]:.4f}")

    print("\nSpecific Check:")
    if 'dog' in inv_map:
        dog_idx = inv_map['dog']
        print(f"dog ({dog_idx}): {preds[dog_idx]:.6f}")
    if 'airplane' in inv_map:
        air_idx = inv_map['airplane']
        print(f"airplane ({air_idx}): {preds[air_idx]:.6f}")


except Exception as e:
    print(f"Error: {e}")
