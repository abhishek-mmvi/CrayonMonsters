import numpy as np
import os
from sklearn.model_selection import train_test_split

DATA_DIR = "data"
IMG_SIZE = 28
MAX_PER_CLASS = 2000

X = []
y = []

class_names = sorted([
    f.replace(".npy", "") for f in os.listdir(DATA_DIR) if f.endswith(".npy")
])

for label, name in enumerate(class_names):
    data = np.load(os.path.join(DATA_DIR, name + ".npy"))
    data = data[:MAX_PER_CLASS]
    X.append(data)
    y.extend([label] * len(data))

X = np.concatenate(X)
y = np.array(y)

# Normalize
X = X.astype("float32") / 255.0
X = X.reshape(-1, IMG_SIZE, IMG_SIZE, 1)

# Proper shuffle + split
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

np.savez("dataset.npz",
         X_train=X_train,
         y_train=y_train,
         X_val=X_val,
         y_val=y_val,
         class_names=class_names)

print("Dataset built correctly.")
print("Classes:", len(class_names))
