import urllib.request
import os

BASE_URL = "https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/"
SAVE_DIR = "data"

os.makedirs(SAVE_DIR, exist_ok=True)

# Broad useful keywords (semantic)
USEFUL_KEYWORDS = [
    # animals
    "cat","dog","bird","fish","horse","cow","sheep","pig",
    "lion","tiger","bear","elephant","giraffe","zebra",
    "monkey","rabbit","frog","snake","turtle",
    "shark","whale","dolphin","octopus",

    # fantasy
    "dragon","mermaid","angel","monster","unicorn",

    # vehicles
    "car","truck","bus","train","airplane","helicopter",
    "motorbike","bicycle","ship","submarine","rocket",

    # buildings
    "house","castle","church","hospital","bridge",
    "skyscraper","lighthouse",

    # tools / weapons
    "sword","axe","hammer","shield","bow","rifle","cannon","drill",

    # tech
    "computer","laptop","keyboard","cell phone","camera",

    # nature
    "tree","mountain","river","ocean","sun","moon","cloud","volcano",

    # beings / body
    "face","hand","skull","person",

    # shapes
    "circle","square","triangle"
]

# Load official categories
with open("categories.txt", "r") as f:
    ALL_CATEGORIES = [line.strip() for line in f]

selected = []
for cat in ALL_CATEGORIES:
    for kw in USEFUL_KEYWORDS:
        if kw == cat.lower():
            selected.append(cat)

print(f"Selected {len(selected)} useful categories")

# Download
for cat in selected:
    filename = cat.replace(" ", "_") + ".npy"
    url = BASE_URL + filename
    try:
        urllib.request.urlretrieve(url, f"{SAVE_DIR}/{filename}")
        print(f"Downloaded: {filename}")
    except:
        print(f"Failed: {filename}")
