[← Back to Home](index.md)

# User Interface

PyQt6-based graphical interface for game interaction and configuration.

**Related Components:** [Game Engine](game_engine.md) | [Hardware Control](hardware_control.md) | [Vision System](vision_system.md) | [Communication](communication.md)

## Overview

The User Interface component is responsible for:
- **Game Visualization** - Display board state and piece positions
- **User Interaction** - Handle move input and game control
- **Settings Management** - Configure system parameters
- **Visual Feedback** - Show status, timers, and notifications
- **Navigation** - Switch between game, settings, and home screens

## Module Documentation

### Main UI Application

The primary application window and navigation system.

::: ui.main_ui
    options:
      docstring_style: google

### Game Page

The main game interface where chess is played.

::: ui.game_page
    options:
      docstring_style: google

### Home Page

The home/welcome screen and game mode selection.

::: ui.home_page
    options:
      docstring_style: google

### Settings Page

Configuration interface for system settings and calibration.

::: ui.settings_page
    options:
      docstring_style: google

### Dialog Components

Popup dialogs for notifications and selections.

::: ui.dialog_ui
    options:
      docstring_style: google

## User Interface Components

### Game Board
- **Visual Representation** - 8x8 chess board with pieces
- **Square Highlighting** - Show selected piece and legal moves
- **Trajectory Display** - Show robot movement path

### Move History
- **Notation List** - Display all moves in algebraic notation
- **Move Navigation** - Step backward/forward through game
- **Capture Indicators** - Mark captured pieces

### Chess Clock
- **Time Display** - Show remaining time for each player
- **Color Indicators** - White/black background for current player
- **Out of Time Detection** - Automatic game end on timeout

### Status Indicators
- **Turn Indicator** - Show which player's turn it is
- **Waiting Spinner** - Show processing status with animated gear
- **Error Messages** - Display issues or invalid moves

### Settings Controls
- **Board Orientation** - Rotate board perspective (possible to play as black or white)
- **Difficulty Selection** - Choose chess engine opponent strength
- **Device Configuration** - Select and test hardware (core XY or camera)

## Game Flow

```
Home Page (Game Mode Selection)
    ↓
Game Page (Play Chess)
    ├─ Human Move Detection
    ├─ Chess Engine Move Generation
    └─ Board Update/Display
    ↓
End Game Dialog (Result)
    ├─ Play Again → Home Page
    └─ Exit → Application Close
```

## Navigation Structure

```
Main Application
├── Home Page
│   ├── Difficulty Choice
│   ├── Color Choice
│   └── Settings Button
├── Game Page
│   ├── Chess Board
│   ├── Move History
│   ├── Chess Clocks
│   ├── Settings Button (Context)
│   ├── Undo Button
│   └── Resign Button
├── Settings Page
│   ├── Core XY Control
│   ├── Camera Calibration and Control
│   └── Magnet Control
└── Dialogs
    ├── Game Over (Win/Draw/Loss)
    ├── Invalid Move Warning
    ├── Promotion Selection
    └── Waiting Indicator
```

## Key Features

- **Responsive Design** - Adapts to different screen sizes
- **Drag & Drop Moves** - Click pieces and drag to destination
- **Keyboard Shortcuts** - Quick access to common functions
- **Undo/Redo** - Review and navigate game history
- **Settings Persistence** - Save preferences between sessions
- **Error Messages** - Clear feedback for user actions
- **Accessible Controls** - Large buttons and readable fonts

## Styling

The interface uses Material Design theme with custom stylesheet (`cnchess_theme.qss`) for consistent visual appearance.

## Usage Example

```python
from main_ui import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

# Create application
app = QApplication(sys.argv)

# Create main window
window = MainWindow()
window.show()

# Run application
sys.exit(app.exec())
```

## Dependencies

- `PyQt6` - GUI framework
- `PyQt6.QtCore` - Core Qt functionality
- `PyQt6.QtGui` - Graphics and icons
- `PyQt6.QtWidgets` - Widget components
- Custom stylesheets (QSS files)
