# EndlessDriver

A 3D endless lane-racing game built from scratch in Python with **PyOpenGL** and **GLUT** — no game engine, no external assets. Every car, tree, coin and raindrop is drawn with raw OpenGL primitives.

Dodge traffic across three lanes, grab coins to charge your turbo, switch between chase-cam and cockpit view, and drive through four different weather moods.

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![PyOpenGL](https://img.shields.io/badge/PyOpenGL-3.1%2B-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## Table of Contents

- [Features](#features)
- [Gameplay](#gameplay)
- [Installation](#installation)
- [Running the Game](#running-the-game)
- [Controls](#controls)
- [How to Play](#how-to-play)
- [Game Systems](#game-systems)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Author](#author)

---

## Features

| | |
|---|---|
| **Infinite procedural road** | Lane markers, roadside grass and 40 recycled trees scroll endlessly toward the player |
| **Smart traffic AI** | Enemy cars have individual speeds, keep a safe following distance, change lanes to overtake, and slow down when boxed in |
| **Coin & turbo economy** | Collect 5 coins to unlock a 5-second turbo: double speed, orange paint job, and temporary invulnerability |
| **Live turbo meter** | HUD bar fills blue while charging, turns green when ready, and drains orange while active |
| **Dual camera modes** | Toggle between an adjustable third-person chase cam and a 90° FOV first-person cockpit view |
| **Four weather modes** | Day, Night, Sunny and Rain — each with its own sky, road and grass palette |
| **Particle rain** | 500 alpha-blended rain streaks that follow the camera and scroll with your speed |
| **Manual speed control** | Throttle up or down on the fly, from 0.5x to as fast as you dare |
| **Pause, restart, quit** | Full game-state handling with an on-screen game-over summary |

---

## Gameplay

```
 +----------------------------------------------------------+
 | Score: 42                   Controls:                     |
 | Speed: 2.0 [TURBO! 3.4s]    A/D - Move | W/S - Speed       |
 | Lane: Middle                T - Turbo  | V - Camera        |
 | Camera: Third Person        Arrow Keys - Camera view       |
 | Weather: Rainy              R - Restart | Q - Quit         |
 |                                            TURBO [######] |
 |                  (tree)            (tree)                 |
 |                 #====|====|====#                          |
 |                 #    | car |    #   <- enemy traffic      |
 |                 # () |     |    #   <- coin               |
 |                 #    | YOU |    #   <- player             |
 |                 #====|====|====#                          |
 +----------------------------------------------------------+
```

> Screenshots and a gameplay GIF go here — drop them in an `assets/` folder and link them.

---

## Installation

### Prerequisites

- **Python 3.7 or newer**
- **PyOpenGL**, with GLUT/freeglut available on your system

### 1. Clone the repository

```bash
git clone https://github.com/UtshaBasak/EndlessDriver.git
cd EndlessDriver
```

### 2. (Recommended) Create a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

**Platform notes for GLUT:**

| Platform | Extra step |
|---|---|
| **Windows** | `pip install PyOpenGL` usually ships the needed DLLs. If GLUT fails to load, install the unofficial PyOpenGL wheels for your Python version, or place `freeglut.dll` next to the script. |
| **Linux (Debian/Ubuntu)** | `sudo apt install freeglut3-dev` |
| **Linux (Fedora)** | `sudo dnf install freeglut-devel` |
| **macOS** | GLUT ships with the OS, but PyOpenGL may need help locating the deprecated GLUT framework on recent releases. |

---

## Running the Game

```bash
python EndlessDriver.py
```

A 1000x800 window titled **EndlessDriver** opens, and the control list is printed to your terminal. The terminal doubles as a running event log — lane changes, speed changes, turbo pickups and weather switches all echo there.

---

## Controls

### Driving

| Key | Action |
|:---:|---|
| <kbd>A</kbd> | Move one lane left |
| <kbd>D</kbd> | Move one lane right |
| <kbd>W</kbd> | Increase speed (+0.5) |
| <kbd>S</kbd> | Decrease speed (-0.5, minimum 0.5) |
| <kbd>T</kbd> | Activate turbo (only when the meter is full) |

### View & Weather

| Key | Action |
|:---:|---|
| <kbd>V</kbd> | Toggle third-person / first-person camera |
| <kbd>Up</kbd> <kbd>Down</kbd> | Raise / lower the chase camera *(third-person only)* |
| <kbd>Left</kbd> <kbd>Right</kbd> | Pan the chase camera sideways *(third-person only)* |
| <kbd>1</kbd> | Day |
| <kbd>2</kbd> | Night |
| <kbd>3</kbd> | Sunny |
| <kbd>4</kbd> | Rain |

### Game State

| Key | Action |
|:---:|---|
| <kbd>P</kbd> | Pause / resume |
| <kbd>R</kbd> | Restart *(only after a crash)* |
| <kbd>Q</kbd> | Quit immediately |

---

## How to Play

1. **Stay alive.** You occupy one of three lanes on an endless highway. Hitting an enemy car ends the run.
2. **Score points.**
   - **+1** every time an enemy car scrolls off behind you
   - **+2** for every coin collected
3. **Charge the turbo.** Collect **5 coins** and the HUD bar turns green — then press <kbd>T</kbd> to burn it.
4. **Use turbo wisely.** For 5 seconds you move at double speed, your car glows orange, and **you cannot crash**. It is your escape hatch out of a blocked lane — and a score multiplier, since traffic flies past faster.
5. **Push your speed.** Higher speed means more cars passed per second, but far less reaction time.
6. **Crash?** Your final score is shown on screen. Press <kbd>R</kbd> to go again.

---

## Game Systems

### Traffic AI

Enemy vehicles are more than moving obstacles — each one runs a small behaviour loop every frame:

- **Individual cruising speed.** Every car gets a `relative_speed` between -0.4 and +0.4 on top of the world speed, so some pull away from you while others drift back toward you.
- **Following distance.** A car detects the nearest vehicle ahead in its own lane. Inside 90 units, it reacts.
- **Overtaking.** It first tries to merge left, then right. A merge is only allowed if the target lane exists and no other car is within 120 units — then a 60-frame cooldown prevents zig-zagging.
- **Braking.** If neither lane is clear, it matches the leader's speed minus 0.2 (floored at -0.8), so traffic bunches up realistically instead of overlapping.

Spawning is guarded too: a new car only appears if its lane is clear for 200 units and the adjacent lanes are clear for 300 units, with at most 2 enemies on screen at a time.

### Coin & Turbo Economy

- Coins spawn in lanes that are not occupied by oncoming traffic, roughly every 100-140 frames with a 30% roll; occasionally two spawn side by side.
- Each coin is a flattened, spinning gold cube.
- Coins are picked up within 50 units of the player in the same lane.
- Turbo is **time-based** (`time.time()`), so its 5-second duration is independent of frame rate. When it expires, the coin counter resets to zero.

### Weather & Rain

Each mode swaps the clear colour, road colour and grass colour:

| Mode | Sky | Feel |
|---|---|---|
| Day | Light blue | Default, neutral |
| Night | Deep navy | Darkened road and grass |
| Sunny | Warm yellow | Washed-out, high-key greens |
| Rain | Grey-blue | Desaturated, plus a particle layer |

Rain uses 500 `RainParticle` objects positioned **relative to the camera**, so the storm follows you in both camera modes. Each streak falls, drifts backwards with the world speed, and respawns above once it exits the volume. Particles are drawn as alpha-blended `GL_LINES` with depth testing disabled, so they always read as a foreground layer.

### Rendering

Everything is immediate-mode OpenGL:

- **Road & grass** — flat `GL_QUADS` at z=0, with dashed lane markers scrolled by a looping `marker_offset`.
- **Player car** — a scaled cube body, a cabin cube, and four `gluCylinder` wheels capped with `gluDisk`. Hidden in first-person so you see through the windscreen.
- **Enemy cars** — body, cabin, bumper, two headlight spheres, two tail-light spheres and four wheels, tinted with a random per-car colour.
- **Trees** — a stretched brown cube trunk and a `gluSphere` canopy. 40 trees loop through a 4000-unit stretch and are re-randomised on the far side of the road each time they recycle.
- **HUD** — `GLUT_BITMAP_HELVETICA_18` text and the turbo bar are drawn in a temporary `gluOrtho2D` projection, pushed and popped around each element.

---

## Project Structure

```
EndlessDriver/
├── EndlessDriver.py    # The entire game (~830 lines)
└── README.md
```

Single file, no assets, no build step. Inside, the code is organised as:

| Section | Contents |
|---|---|
| **Config constants** | Road/lane dimensions, camera positions, turbo tuning, spawn spacing, weather settings |
| **`EnemyVehicle`** | Traffic entity — movement, lane-change validation, off-screen check |
| **`Coin`** | Collectible — scroll, spin, off-screen check |
| **`RainParticle`** | Camera-relative rain streak — fall, drift, respawn |
| **Update functions** | `update_game`, `update_enemies`, `update_coins`, `update_turbo`, `update_weather`, `update_dynamic_trees`, `update_player_position` |
| **Draw functions** | `draw_road`, `draw_player_car`, `draw_enemy_vehicle`, `draw_coin`, `draw_tree`, `draw_rain`, `draw_turbo_bar`, `draw_text` |
| **Input handlers** | `keyboard` (ASCII keys), `special_key` (arrow keys) |
| **GLUT plumbing** | `setup_camera`, `show_screen`, `idle`, `main` |

---

## Configuration

Tweak the constants at the top of [EndlessDriver.py](EndlessDriver.py) to change the feel of the game:

```python
ROAD_LENGTH = 1200          # How far the road stretches in front and behind
LANE_WIDTH  = 150           # Distance between lane centres

TRANSITION_SPEED = 8        # How snappy lane changes feel

TURBO_DURATION  = 5.0       # Seconds of boost
COINS_FOR_TURBO = 5         # Coins needed to charge it

MIN_SPAWN_DISTANCE = 200    # Same-lane clearance required to spawn a car
MIN_LANE_GAP       = 300    # Adjacent-lane clearance required to spawn a car

NUM_TREES               = 40   # Roadside tree count
TREE_DISTANCE_FROM_ROAD = 200  # How far back the treeline sits

NUM_RAIN_PARTICLES = 500    # Lower this if rain costs you frames
RAIN_SPEED         = 8      # How hard it is coming down
```

Want denser traffic? Raise the `len(enemy_vehicles) < 2` limit in `spawn_enemy()`. Want a harder run? Lower `MIN_SPAWN_DISTANCE`.

---

## Troubleshooting

<details>
<summary><strong>ImportError: No module named OpenGL</strong></summary>

PyOpenGL is not installed in the interpreter you are running. Activate your virtual environment and run `pip install PyOpenGL PyOpenGL_accelerate`.
</details>

<details>
<summary><strong>OSError: attempt to call an undefined function glutInit / "Please install freeglut"</strong></summary>

Python found PyOpenGL but not the GLUT library itself.

- **Windows:** install a PyOpenGL wheel that bundles GLUT, or place `freeglut.dll` (matching your Python's 32/64-bit build) beside `EndlessDriver.py`.
- **Linux:** `sudo apt install freeglut3-dev`, or your distro's equivalent.
- **macOS:** GLUT is part of the OS, but PyOpenGL may need help locating the framework on newer releases.
</details>

<details>
<summary><strong>The window opens black or nothing is drawn</strong></summary>

Usually a driver or software-renderer issue. Make sure your GPU drivers are current, and if you are on a VM or remote desktop, enable 3D/hardware acceleration.
</details>

<details>
<summary><strong>Rain makes the game stutter</strong></summary>

Lower `NUM_RAIN_PARTICLES` from 500 to 150-200, or install `PyOpenGL_accelerate`.
</details>

<details>
<summary><strong>Keys do not respond</strong></summary>

Click the game window to give it focus. Also note: <kbd>R</kbd> only works after a crash, and the arrow keys only move the camera in third-person mode.
</details>

---

## Roadmap

Ideas for anyone who wants to extend the game:

- [ ] Persistent high-score table saved to disk
- [ ] Automatic weather cycling (the `weather_transition_timer` / `WEATHER_CYCLE_TIME` hooks are already reserved)
- [ ] Progressive difficulty — speed ramps up with distance travelled
- [ ] Sound effects and background music
- [ ] Smooth lateral interpolation for enemy lane changes (they currently snap)
- [ ] Extra power-ups: shields, coin magnets, slow-motion
- [ ] Headlight cones and reflections in night mode
- [ ] A start menu and difficulty selection

---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch — `git checkout -b feature/your-feature`
3. Commit your changes — `git commit -m "Add your feature"`
4. Push the branch — `git push origin feature/your-feature`
5. Open a Pull Request

Please keep the project dependency-free beyond PyOpenGL, and match the existing code style.

---

## Author

**Utsha Basak** — [@UtshaBasak](https://github.com/UtshaBasak)

Project: <https://github.com/UtshaBasak/EndlessDriver>

---

## License

No license file is currently included, so all rights are reserved by the author by default. If you want this to be open source, adding an [MIT License](https://choosealicense.com/licenses/mit/) is the usual next step.

---

<p align="center">
  <i>Built with Python, PyOpenGL and a lot of glPushMatrix.</i><br>
  Star the repo if you enjoyed it!
</p>
