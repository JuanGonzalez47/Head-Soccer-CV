# 🧠 Head Soccer — Computer Vision Controlled Edition

This project is an experimental fork of [Old Head Soccer](https://github.com/Nicolasbort/# Head Soccer Game with Computer Vision Control 🎮

A Python-based 2D soccer game where players can control their characters using computer vision (head movements) or keyboard controls.

## 🌟 Features

### Dual Control Systems
- 🎥 **Computer Vision Control**: Control players with head movements
- ⌨️ **Keyboard Control**: Traditional keyboard controls as fallback

### Game Mechanics
- ⚽ Physics-based ball movement with realistic parabolic trajectories
- 🎯 Head and kick actions for both players
- 💥 Real-time collision detection
- 📊 Score tracking system
- 🏃‍♂️ Smooth player movements

### Technical Implementations
- 🔄 Optimized game loop for smooth gameplay
- 🎯 Precise collision detection system
- 📐 Realistic physics for ball movement
- 🎮 Responsive controls

## ⚙️ Tech Stack

- **Python 3.9+**
- **graphics.py** – for rendering the original 2D game
- **OpenCV** – webcam capture and image processing
- **Mediapipe** – body, hand, and pose detection
- **NumPy** – optional for data smoothing or calculations
- **playsound** / **Pillow** – from original ga

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/JuanGonzalez47/Head-Soccer-CV.git
```
2. Activate your virtual environment:
```bash
.\venv310\Scripts\Activate.ps1
```
3. Install required packages:
```bash
pip install -r requirements.txt
```
## 🎮 How to Play

1. Run the game:
```bash
python -m src.core.game
```

### Controls:

#### Keyboard Controls:
- **Player 1:**
  - Movement: Arrow keys (← →)
  - Jump/Header: Up arrow (↑)
  - Kick: Down arrow (↓)

- **Player 2:**
  - Movement: A/D keys
  - Jump/Header: W key
  - Kick: S key

#### Computer Vision Controls:
- Up or Close your hand left/right to control player movement (Right Hand)
- Move your left hand up to jump
- To kick the ball up your knee

## 🔧 Recent Updates

- Fixed game freezing issues
- Optimized ball physics and player movements
- Balanced header and kick powers for better gameplay
- Improved collision detection
- Added consistent parabolic trajectories for headers
- Fine-tuned game mechanics for better control

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Authors

- [JuanGonzalez47](https://github.com/JuanGonzalez47)), redesigned to explore **human-motion control** using **computer vision**.
