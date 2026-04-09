[← Back to Home](index.md)

# Communication Layer

Device communication for ESP32 and hardware control via PySerial.

**Related Components:** [Game Engine](game_engine.md) | [Hardware Control](hardware_control.md) | [Vision System](vision_system.md) | [UI](user_interface.md)

## Overview

The Communication Layer component is responsible for:
- **Serial Communication** - Establish connection with microcontroller
- **Protocol Handling** - Encode/decode command messages
- **Command Transmission** - Send movement and control commands
- **Status Monitoring** - Receive and interpret device feedback
- **Error Handling** - Manage communication failures gracefully

## Module Documentation

### Communication Module

The serial communication system for hardware device control.

::: Communication
    options:
      docstring_style: google

## Key Features

- **Robust Serial Protocol** - Reliable communication with error checking
- **Asynchronous Operation** - Non-blocking command transmission
- **Auto-reconnection** - Handle disconnections gracefully
- **Timeout Management** - Prevent hanging on failed commands

## Architecture

```
Communication Layer
├── Serial Port Management
│   ├── Port Detection
│   └── Connection State
├── Command Protocol
│   ├── Command Encoding
│   └── Parameter Packing
├── Response Handling
│   ├── Message Parsing
│   └── Error Detection
└── Device Interface
    ├── Gantry Movement Status
    └── Servo State Feedback
```

## Command Protocol

### Message Format

```
[COMMAND] [PARAMETERS] <>

        1 byte    variable     1 byte    0xFF
```

### Common Commands

- **HOME** - Move gantry to home position
- **MOVE** - Execute X,Y absolute movement command 
- **JOG** - Execute X,Y relative movement command  
- **SERVO** - Control up down of effector to manipulate pieces (magnet)
- **STOP** - Stop gantry 
- **CHESSMOVE** - Send command as grid coordinate with effector state
- **PATH** - Send complete sets of command to execute a complete chess move

## Communication Flow

1. **Initialization** - Detect and connect to device
2. **Handshake** - Verify device is responsive
3. **Command Send** - Transmit movement commands
4. **Status Check** - Wait for completion
5. **Error Handling** - Retry or abort as needed
6. **Disconnection** - Clean shutdown

## Serial Configuration

```python
from Communication import Communication

# Initialize communicator
comm = Communication()

# Send command
comm.send_path(path_commands)

# Wait for button press (human move)
comm.wait_for_button_press()

```
## Dependencies

- `PySerial` - Serial port communication
- Microcontroller firmware (ESP32/Arduino)

