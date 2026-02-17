<<<<<<< HEAD
# Gesture Dino

A real-time gesture-controlled recreation of the Chrome Dinosaur game, built with Python. The player controls the dinosaur entirely through hand gestures detected via webcam using computer vision — no keyboard required.

---

## Overview

Gesture Dino uses **MediaPipe Hands** for real-time hand landmark detection and **Pygame** for game rendering. The camera feed is embedded directly inside the game window as a picture-in-picture overlay, so no secondary window is opened. The game includes light and dark themes, progressive speed scaling, flying pterodactyl obstacles, particle effects, and a persistent high score display.

---

## Features

- Real-time hand gesture recognition via webcam
- Three distinct gesture controls: jump, duck, and neutral run
- Embedded camera feed (top-right corner of the game window)
- Light and dark theme with a toggle button
- Six cactus obstacle variants with shading
- Pterodactyl obstacles that appear after score 300, requiring the player to duck
- Dust particle effects on landing and death
- Progressive speed increase matching the original Chrome Dino behavior
- HI score tracking with milestone flash every 100 points
- Keyboard fallback controls for all actions

---

## Project Structure

```
Gesture-Dino/
├── main.py                  # Game loop, rendering, UI
├── dino.py                  # Player character logic and drawing
├── obstacles.py             # Cactus and pterodactyl classes, obstacle manager
├── gesture_controller.py    # Hand detection and gesture classification
├── config.py                # All constants, theme colors, physics values
├── requirements.txt         # Python dependencies
└── README.md
```

---

## Requirements

- Python 3.8 or higher
- A working webcam
- The following Python packages (see `requirements.txt`):

| Package | Purpose |
|---|---|
| pygame | Game window, rendering, input |
| opencv-python | Webcam capture, frame processing |
| mediapipe | Hand landmark detection |
| numpy | Array operations for frame handling |

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/Ishika-guptaa25/Gesture-Dino.git
cd Gesture-Dino
```

**2. Create a virtual environment (recommended)**

```bash
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Run the game**

```bash
python main.py
```

---

## How to Play

- The dinosaur runs automatically. Your job is to avoid obstacles.
- Use hand gestures in front of your webcam to control the dinosaur.
- The game speed gradually increases as your score rises.
- Cacti must be jumped over. Pterodactyls appear at score 300 and must be ducked under.
- The game ends on collision. Your high score is retained until the window is closed.

---

## Gesture Reference

Hold your hand clearly in front of the camera. Gestures are classified each frame.

| Gesture | Description | Action      |
|---|---|-------------|
| L-shape | Thumb extended outward, index finger pointing up, remaining fingers curled | Jump        |
| Fist | All four fingers and thumb fully curled closed | Bend |
| Pinch | Thumb tip and index tip brought close together | Neutral / run |

**Tips for reliable detection:**
- Use in a well-lit environment
- Keep your hand within the camera frame
- Face the palm toward the camera
- Avoid fast erratic movements

---

## Keyboard Controls

All gestures have keyboard equivalents if the camera is unavailable.

| Key | Action |
|---|---|
| Space or Up Arrow | Jump |
| Down Arrow | Duck (hold) |
| Escape | Quit |

The theme toggle button is clickable with the mouse (top-right area of the window, below the camera feed).

---

## Configuration

All tunable values are in `config.py`. Key settings:

| Constant | Default | Description |
|---|---|---|
| `WIDTH` | 1200 | Game window width in pixels |
| `HEIGHT` | 520 | Game window height in pixels |
| `GRAVITY` | 1.1 | Downward acceleration per frame |
| `JUMP_VEL` | -20 | Initial vertical velocity on jump |
| `SPEED_START` | 8.0 | Starting game speed |
| `SPEED_MAX` | 22.0 | Maximum game speed cap |
| `SPEED_INC` | 0.004 | Speed increase per score point |

Theme colors for both light and dark modes are also defined in `config.py` under the `THEMES` dictionary and can be customized freely.

---

=======
# Gesture-Dino
under process
>>>>>>> c77737fd7bab972f497b8cc5d108da1d599d62d0

