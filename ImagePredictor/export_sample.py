import numpy as np
from PIL import Image
import os

# Load dataset
data = np.load("dataset.npz", allow_pickle=True)
X_train = data["X_train"]
y_train = data["y_train"]
class_names = data["class_names"]

def save_sample(class_name, filename):
    try:
        # Find index for the class
        class_idx = np.where(class_names == class_name)[0][0]
        
        # Find all images of this class
        indices = np.where(y_train == class_idx)[0]
        
        # Pick a random one
        idx = indices[0] # Just pick the first one for consistency
        
        # Get image data (28, 28, 1) -> (28, 28)
        img_arr = X_train[idx].reshape(28, 28)
        
        # Convert to 0-255
        # Note: Dataset is White strokes on Black background (values 0..1)
        img_uint8 = (img_arr * 255).astype(np.uint8)
        
        # Invert it for the USER (Black strokes on White paper)
        # Because our test_single_image.py expects "drawing on paper" and inverts it back.
        # If we save strictly raw (white on black), the user might be confused why it looks "negative".
        # Let's save it as a "Normal Drawing" (Black on White).
        img_uint8_inverted = 255 - img_uint8
        
        Image.fromarray(img_uint8_inverted).save(filename)
        print(f"Saved {filename} (Class: {class_name})")
        
    except IndexError:
        print(f"Class '{class_name}' not found in dataset.")

# Export a few examples
save_sample("dog", "sample_dog.png")
save_sample("airplane", "sample_airplane.png")
save_sample("bridge", "sample_bridge.png")
