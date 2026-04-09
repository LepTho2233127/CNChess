[← Back to Home](../index.md)

# Vision System

Computer vision for board detection and piece position recognition.

**Related Components:** [Game Engine](game_engine.md) | [Hardware Control](hardware_control.md) | [Communication](communication.md) | [UI](user_interface.md)

## Overview

The Vision System component is responsible for:
- **Image Capture** - Retrieve frames from camera
- **Board Detection** - Identify chess board boundaries and orientation
- **Piece Recognition** - Locate individual pieces and their positions
- **Move Detection** - Determine what move was made from before/after images
- **Optical Validation** - Verify game state matches expectations

## Module Documentation

### Camera Module

The computer vision system for board and piece detection.

::: Cam
    options:
      docstring_style: google

## Key Features

- **Real-time Processing** - Fast image analysis for smooth gameplay
- **Piece Classification** - Identify piece type and color
- **Board Orientation** - Automatic detection of board perspective
- **Lighting Adaptation** - Handle varying lighting conditions
- **Calibration Support** - Customizable calibration points for accuracy
- **Move Validation** - Verify moves match detected piece movements

## Architecture

```
Vision System
├── Camera Interface
│   ├── Frame Capture
│   ├── Resolution: 1280x960
│   └── Stabilization
├── Board Detection
│   ├── Edge Detection
│   ├── Board Boundaries
│   └── Square Identification
├── Piece Recognition
│   ├── Color Detection
│   ├── Piece Type Classification
│   └── Position Mapping
└── Move Analysis
    ├── Before/After Comparison
    ├── Piece Movement Tracking
    └── FEN Generation
```

## Image Processing Pipeline

1. **Capture** - Get frame from camera
2. **Preprocessing** - Apply color correction and normalization
3. **Board Detection** - Identify board grid and squares
4. **Piece Segmentation** - Extract individual pieces from squares
5. **Classification** - Determine piece type and color
6. **Position Mapping** - Convert pixel coordinates to chess notation
7. **Move Detection** - Compare with previous board state

## Calibration

The system requires calibration points for accurate position mapping:

```python
from Cam import Cam

# Initialize camera
cam = Cam()

# Calibration points format
# Maps chess board positions to pixel coordinates
calibration_points = {
    'a1': (x1, y1),
    'a8': (x2, y2),
    'h1': (x3, y3),
    'h8': (x4, y4),
    # ... additional calibration points
}
```

## Lighting Requirements

- **Optimal Lighting** - Uniform, consistent lighting across board
- **Avoid Glare** - Position camera to minimize reflections
- **Shadow Reduction** - Maintain even illumination
- **Color Accuracy** - Calibrate white balance for piece detection

## Usage Example

```python
from Cam import Cam

# Initialize camera
cam = Cam()

# Capture and process image
result = cam.process_image()

# Result contains:
# - Board state (FEN)
# - Detected move (UCI notation)
# - Confidence score
# - Raw image data

print(f"Detected move: {result['move']['uci']}")
print(f"Board state: {result['board_state']}")
```

## Dependencies

- `OpenCV` - Computer vision processing
- `NumPy` - Image manipulation
- `Camera hardware` - USB or integrated camera
- Calibration data file