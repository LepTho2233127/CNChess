[← Back to Home](../index.md)

# Hardware Control

Robot control systems for movement, positioning, and piece manipulation.

**Related Components:** [Game Engine](game_engine.md) | [Vision System](vision_system.md) | [Communication](communication.md) | [UI](user_interface.md)

## Overview

The Hardware Control component is responsible for:
- **Pathfinding & Trajectory Planning** - Calculate optimal robot paths
- **Gantry Movement** - Control X/Y axis movements
- **Servo Control** - Manage piece picking and placement
- **Position Calculations** - Convert board coordinates to robot coordinates

## Module Documentation

### Control Module

The core control system for robot movement and path planning.

::: Control
    options:
      docstring_style: google

## Key Features

- **Intelligent Pathfinding** - Efficient path calculation avoiding collisions
- **Board Coordinate Conversion** - Transform chess board positions to robot coordinates
- **Trajectory Optimization** - Smooth movement paths with minimal positioning time
- **Servo Management** - Automated piece manipulation with magnet control
- **Home Position Homing** - Return to safe home position
- **Movement Validation** - Ensure all moves are within robot workspace

## Architecture

```
Hardware Control
├── Pathfinding Engine
│   ├── Start Position
│   ├── Destination Position
│   └── Path Generation
├── Movement Commands
│   ├── Gantry Movement (X, Y)
│   ├── Speed Control
│   └── Servo Operations
└── Coordinate Systems
    ├── Chess Board (A-H, 1-8)
    ├── Robot Space (mm)
    └── Calibration Points
```

## Movement Workflow

1. **Piece Selection** - Identify source square from game engine
2. **Target Calculation** - Determine destination square
3. **Path Planning** - Generate robot movement path
4. **Execution** - Send commands to hardware controller
5. **Verification** - Confirm piece placement
6. **Return Home** - Move gantry to safe position

## Coordinate Systems

### Chess Board Coordinates
- Columns: A-H (Left to Right)
- Rows: 1-8 (Bottom to Top)
- Example: e4 (King's Pawn opening)

### Robot Coordinates
- X-Axis: Left-Right (mm)
- Y-Axis: Forward-Back (mm)
- Calibration required for accurate mapping

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

# Execute movement
for command in path:
    control.send_command(command)

# Print path details
control.print_path(path)
```

## Dependencies

- Robot hardware drivers
- Calibration data
- Communication interface to microcontroller