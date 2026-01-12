"""
CrayonMonsters Game Configuration
"""
import os
import socket

# Server Settings
HOST = '0.0.0.0'  # Bind to all interfaces (allows LAN connections)
PORT = 5002  # Changed from 5000 (often used by AirPlay)
SECRET_KEY = 'crayon-monsters-secret-key-change-in-production'

# Database
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'game.db')

# Game Settings
DRAW_TIME_SECONDS = 180  # 3 minutes
CREATURES_PER_PLAYER = 3
CANVAS_SIZE = 400

# Paths to other modules
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IMAGE_PREDICTOR_PATH = os.path.join(BASE_DIR, 'ImagePredictor')
STATGEN_PATH = os.path.join(BASE_DIR, 'StatGen')

def get_lan_ip():
    """Get the LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LAN_IP = get_lan_ip()
