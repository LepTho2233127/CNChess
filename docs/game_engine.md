[← Back to Home](index.md)

# Game Engine

The core game engine that handles game logic, move validation, and the chess engine decision-making.

**Related Components:** [Hardware Control](hardware_control.md) | [Vision System](vision_system.md) | [Communication](communication.md) | [UI](user_interface.md)

## Overview

The Game Engine component is responsible for:
- **Game State Management** - Maintaining board positions and game history
- **Move Validation** - Ensuring all moves follow chess rules
- **Chess engine Decision Making** - Generating computer player moves
- **Game Outcome Detection** - Detecting checkmate, stalemate, and draw conditions
- **Choosing difficulty level** - Easy, medium or hard

## Module Documentation

### Main Entry Point

The main application entry point that initializes the entire system.

::: main
    options:
      docstring_style: google

### Chess Game Engine

The core chess game logic and state management system. It uses python `chess` library and Stockfish chess engine at various difficulties.

::: CNChess
    options:
      docstring_style: google

## Key Features

- **FEN Support** - Full Forsyth-Edwards Notation support for board representation
- **Move Legality** - Complete validation of chess move rules
- **Game History** - Track all moves with ability to undo/redo
- **Chess engine Opponent** - Computer player with configurable difficulty (easy, medium or hard)
- **Promotion Handling** - Automatic pawn promotion on reach of last rank
- **Check/Checkmate Detection** - Real-time detection of game-ending conditions

## Architecture

```
Game Engine
├── Board State (FEN)
├── Move Validation
│   ├── Legal Moves Generator
│   ├── Rule Enforcement
│   └── Special Moves (Castling, En Passant, Promotion)
├── Chess Engine Decision Making
└── Game Outcome
    ├── Checkmate Detection
    └── Draw Detection
```

## Usage Example

```python
from CNChess import CNChess

# Initialize the game
chess_game = CNChess()

# Get current board state
board_state = chess_game.get_board_state()

# Get legal moves for a piece
legal_moves = chess_game.get_legal_moves_from_square('e2')

# Validate and make a move
move = chess.Move.from_uci('e2e4')
if chess_game.validate_move(move):
    chess_game.make_move(move)

# Get chess engine move
best_move = chess_game.get_next_best_move()
```

## Dependencies

- `chess` - Python chess library for game logic
- `Python 3.8+` - Core language
