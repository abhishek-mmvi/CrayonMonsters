# 🖍️ CrayonMonsters

**Draw your monsters. Battle your friends.**

CrayonMonsters is a multiplayer turn-based battle game where players draw their own creatures, and AI brings them to life with unique stats and abilities. Think Pokémon meets Pictionary!

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-orange.svg)
![Flask](https://img.shields.io/badge/Flask-SocketIO-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎮 How It Works

1. **Draw** — Sketch your creature on the canvas
2. **AI Recognition** — A CNN model identifies what you drew (Dragon? Sword? Cat?)
3. **Stat Generation** — An LLM generates unique stats, moves, and abilities based on your drawing
4. **Battle** — Challenge other players in real-time turn-based combat!

---

## ✨ Features

- 🎨 **Draw-to-Play** — Create your own monsters by drawing them
- 🧠 **AI-Powered Recognition** — CNN trained on 300+ categories from Google Quick, Draw!
- ⚔️ **Turn-Based Combat** — Pokémon-style battles with stats, moves, and elemental natures
- 🌐 **LAN Multiplayer** — Play with friends on your local network
- 🤖 **LLM Stat Generation** — Groq API (Llama 3.3) creates unique creature abilities

---

## 🏗️ Project Structure

```
CrayonMonsters/
├── Game/                    # Main game server
│   ├── server.py           # Flask + SocketIO server
│   ├── battle_engine.py    # Turn-based combat logic
│   ├── database.py         # User accounts & match history
│   ├── templates/          # HTML templates (lobby, battle, draw)
│   └── static/             # CSS, sounds, sprites
│
├── ImagePredictor/          # Doodle recognition AI
│   ├── doodle_model.h5     # Trained CNN model
│   ├── train_model.py      # Model training script
│   ├── categories.txt      # 300+ drawable categories
│   └── draw_test/          # Standalone drawing test app
│
├── StatGen/                 # Creature stat generation
│   ├── llm_client.py       # Groq API integration
│   ├── stat_engine.py      # Rule validation engine
│   └── stat_rules.json     # Game balance rules
│
└── DB/                      # Database files
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/abhishek-mmvi/CrayonMonsters.git
   cd CrayonMonsters
   ```

2. **Install dependencies**
   ```bash
   pip install flask flask-socketio bcrypt tensorflow pillow numpy requests
   ```

3. **Set up environment variables**
   ```bash
   # For stat generation (optional but recommended)
   export GROQ_API_KEY="your_groq_api_key_here"
   ```

4. **Initialize the database**
   ```bash
   cd Game
   python database.py
   ```

5. **Start the server**
   ```bash
   python server.py
   ```

6. **Play!**
   - Open the URL shown in terminal (e.g., `http://192.168.1.100:5000`)
   - Share the URL with friends on your network
   - Create accounts and battle!

---

## 🎯 Game Mechanics

### Creature Stats

| Stat | Description |
|------|-------------|
| **HP** | Health points |
| **Attack** | Damage output multiplier |
| **Defense** | Damage reduction |
| **Speed** | Determines turn order |
| **Nature** | Elemental type (fire, water, electric, etc.) |

### Natures (Elements)

`normal` · `fire` · `water` · `electric` · `earth` · `air` · `ice` · `poison` · `metal` · `dark` · `light`

### Moves

Each creature has **4 moves** with different effects:

- **Damage** — Deal direct damage
- **Stat Buff** — Boost your own stats
- **Stat Debuff** — Lower enemy stats
- **Skip Turn** — Chance to stun the opponent
- **Heal** — Restore HP

---

## 🧠 The AI Pipeline

### 1. Image Recognition (ImagePredictor)

- **Model**: Convolutional Neural Network (CNN)
- **Input**: 28×28 grayscale images
- **Training Data**: Google Quick, Draw! dataset
- **Categories**: 300+ objects (dragon, sword, cat, castle, etc.)

The smart preprocessing pipeline handles:
- Auto-cropping drawings from large canvases
- Contrast enhancement for faint lines
- Color inversion (paper → AI format)

### 2. Stat Generation (StatGen)

- **LLM**: Llama 3.3 70B via Groq API
- **Process**: AI invents creative stats and moves based on the recognized creature
- **Validation**: Engine enforces game balance rules

---

## 🛠️ Development

### Training a New Model

```bash
cd ImagePredictor

# Download training data
python download_data.py

# Build dataset
python build_dataset.py

# Train the model
python train_model.py
```

### Adding New Categories

1. Edit `ImagePredictor/categories.txt`
2. Re-run `download_data.py` and `build_dataset.py`
3. Re-train the model

### Testing the Drawing Interface

```bash
cd ImagePredictor/draw_test
python backend.py
# Open http://localhost:5001
```

---

## 📖 Documentation

- [Server Guide](Game/docs/SERVER_GUIDE.md) — Detailed server setup & management
- [Design Spec](StatGen/design_spec.txt) — Game mechanics & stat system design

---

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM stat generation | Optional* |

*Without the API key, the game will use fallback stat generation.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- [Google Quick, Draw!](https://quickdraw.withgoogle.com/data) — Training data for doodle recognition
- [Groq](https://groq.com/) — Fast LLM inference API
- [TensorFlow](https://tensorflow.org/) — Machine learning framework

---

<p align="center">
  <b>Draw. Battle. Win.</b><br>
  Made with ❤️ and lots of doodles
</p>
