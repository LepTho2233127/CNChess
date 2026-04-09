# CNChess Documentation

Welcome to the CNChess documentation! This is an automated chess playing robot that uses computer vision and robotic control to play chess games.

## System Overview

The CNChess system is divided into five main component groups. Each component has its own dedicated documentation page:

### [Game Engine](components/game_engine.md)
Chess logic and AI decision-making. Handles game state, move validation, and opponent strategy.

### [Hardware Control](components/hardware_control.md)
Robot movement and positioning system. Controls gantry movements, servo operations, and trajectory planning.

### [Vision System](components/vision_system.md)
Computer vision for board detection. Processes camera input to recognize piece positions and moves.

### [Communication Layer](components/communication.md)
Device communication protocol. Manages serial communication with ESP32 and hardware control.

### [User Interface](components/user_interface.md)
PyQt6-based graphical interface. Provides game interaction, settings configuration, and visual feedback.

## System Architecture

```
User Input (UI)
    ↓
Game Engine (Chess Logic)
    ↓
Control Module (Path Planning)
    ↓
Communication (Send to Device)
    ↓
Hardware (Robot Movement)
    ↓
Camera (Detect Result)
    ↓
Update Game State (UI Display)
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`
3. Configure hardware settings through the UI
4. Play chess against the AI or in multiplayer mode

## System Requirements

- Python 3.8+
- PyQt6
- OpenCV for vision processing
- PySerial for device communication
- Chess library for game logic
