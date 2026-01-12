# CrayonMonsters Server Guide

A complete guide to running and maintaining the CrayonMonsters multiplayer game server.

---

## Prerequisites

Before running the server, make sure you have:

1. **Python 3.10+** installed
2. **pip** (Python package manager)

### Quick Check
Open Terminal and run:
```bash
python3 --version
```
You should see something like `Python 3.12.x`.

---

## Installation (One-Time Setup)

### Step 1: Navigate to the Game Directory
```bash
cd /path/to/CrayonMonsters/Game
```

### Step 2: Install Dependencies
```bash
pip install flask flask-socketio bcrypt tensorflow pillow numpy requests
```

### Step 3: Initialize the Database
```bash
python3 database.py
```
This creates `game.db` with the user accounts table.

---

## Starting the Server

### Step 1: Navigate to the Game Directory
```bash
cd /path/to/CrayonMonsters/Game
```

### Step 2: Run the Server
```bash
python3 server.py
```

### Step 3: Note the Server Address
You'll see output like:
```
==================================================
  CrayonMonsters Game Server
==================================================
  LAN IP: 192.168.1.100
  Port:   5000
  URL:    http://192.168.1.100:5000
==================================================
```

### Step 4: Share the URL
Other players on the same network can connect by entering that URL in their browser.

---

## Connecting as a Player

1. Open a web browser (Chrome, Firefox, Safari, etc.)
2. Go to the server URL, e.g., `http://192.168.1.100:5000`
3. Create an account or login
4. Challenge other online players!

---

## Stopping the Server

Press `Ctrl + C` in the Terminal where the server is running.

---

## Database Management

The database file is `Game/game.db`. Here's how to manage it:

### Backup the Database
```bash
cp game.db game_backup.db
```

### Reset the Database (Delete All Users)
```bash
rm game.db
python3 database.py
```

### View Users (Requires SQLite)
```bash
sqlite3 game.db "SELECT id, username, created_at FROM users;"
```

### View Match History
```bash
sqlite3 game.db "SELECT * FROM match_history;"
```

---

## Troubleshooting

### "Module not found" Error
Run:
```bash
pip install flask flask-socketio bcrypt tensorflow pillow numpy requests
```

### "Address already in use" Error
Another process is using port 5000. Either:
- Close that process, or
- Edit `config.py` and change `PORT = 5000` to another number (e.g., 5001)

### Players Can't Connect
1. Make sure all players are on the same WiFi network
2. Check if your firewall is blocking port 5000
3. Try disabling the firewall temporarily

### AI Not Working (Generic Creatures)
This happens if the ImagePredictor model or StatGen can't load. Check:
1. `ImagePredictor/doodle_model.h5` exists
2. `ImagePredictor/label_map.npy` exists
3. `StatGen/stat_rules.json` exists
4. The Groq API key in `StatGen/llm_client.py` is valid

---

## Configuration

Edit `Game/config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `PORT` | 5000 | Server port |
| `DRAW_TIME_SECONDS` | 180 | Drawing phase duration (3 mins) |
| `CREATURES_PER_PLAYER` | 3 | Creatures per team |

---

## File Structure

```
Game/
├── server.py          # Main server (run this!)
├── database.py        # User account management
├── battle_engine.py   # Combat logic
├── config.py          # Server settings
├── game.db            # User database (created on first run)
├── templates/         # HTML pages
│   ├── login.html
│   ├── lobby.html
│   ├── draw.html
│   ├── team.html
│   └── battle.html
├── static/
│   └── style.css      # Retro theme
└── docs/
    └── SERVER_GUIDE.md # This file!
```

---

## Need Help?

If something isn't working:
1. Check the Terminal for error messages
2. Make sure all dependencies are installed
3. Try restarting the server
4. Reset the database if accounts are corrupted

---

**Have fun battling!** 🖍️⚔️
