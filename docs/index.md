# CNChess Documentation

Welcome to the CNChess documentation! This is an automated chess playing robot that uses computer vision and robotic control to play chess games.

## System Overview

The CNChess system is divided into five main component groups. Each component has its own dedicated documentation page:

### [Game Engine](game_engine.md)
Chess logic and chess engine decision-making. Handles game state, move validation, and opponent strategy.

### [Hardware Control](hardware_control.md)
Robot movement and positioning system. Controls gantry movements, servo operations, and trajectory planning.

### [Vision System](vision_system.md)
Computer vision for board detection. Processes camera input to recognize piece positions and moves.

### [Communication Layer](communication.md)
Device communication protocol. Manages serial communication with ESP32 and hardware control.

### [User Interface](user_interface.md)
PyQt6-based graphical interface. Provides game interaction, settings configuration, and visual feedback.

## System Architecture

```
User Input (Button Press)
    ↓
Camera (Detect Result)
    ↓
Game Engine (Validate Move and Calculates Computer Move)
    ↓
Control Module (Path Planning)
    ↓
Communication (Send to Device)
    ↓
Hardware (Robot Movement)
    ↓
Update Game State (UI Display)
```

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python main.py`
3. Configure hardware settings through the UI
4. Play chess against the chess engine 

## System Requirements

- Python 3.8+
- PyQt6
- OpenCV for vision processing
- PySerial for device communication
- Chess library for game logic
- Stockfish 14.1
