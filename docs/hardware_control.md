[← Back to Home](index.md)

# Hardware Control

Robot control systems for movement, positioning, and piece manipulation.

**Related Components:** [Game Engine](game_engine.md) | [Vision System](vision_system.md) | [Communication](communication.md) | [UI](user_interface.md)

## Overview

The Hardware Control component is responsible for:
- **Pathfinding & Trajectory Planning** - Calculate optimal robot paths from as grid coordinates
- **Servo Control** - Manage piece picking and placement

## Module Documentation

### Control Module

The core control system for robot movement and pathfinding.

::: Control
    options:
      docstring_style: google

## Key Features

- **Intelligent Pathfinding** - Efficient path calculation avoiding collisions using A* algorithm
- **Servo Management** - Automated piece manipulation with magnet control

## Architecture

```
Hardware Control
├── Pathfinding Engine
│   ├── Start Position
│   ├── Destination Position
│   └── Path Generation
└── Movement Commands
    ├── Grid Positions
    └── Servo Operations


## Coordinate Systems

### Chess Board Coordinates
- Columns: A-H (Left to Right)
- Rows: 1-8 (Bottom to Top)
- Example: e4 (King's Pawn opening)

### Grid Coordinates
- Grid double the size of chess board (16x16), so the pieces can be moved in between the squares. (0,0) represents the bottom left corner
- Calibration required to the bottom left corner for accurate mapping

## Usage Example

```python
from Control import Control
import chess

# Initialize control system
control = Control()

# Home the robot
control.go_home()

# Get path for a move
move = chess.Move.from_uci('e2e4')
path = control.get_path(move, board_state)
```

