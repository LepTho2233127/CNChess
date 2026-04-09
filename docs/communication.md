[← Back to Home](index.md)

# Communication Layer

Device communication protocol for ESP32 and hardware control.

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
- **Command Buffering** - Queue multiple commands for execution
- **Status Polling** - Monitor device status and feedback
- **Auto-reconnection** - Handle disconnections gracefully
- **Timeout Management** - Prevent hanging on failed commands

## Architecture

```
Communication Layer
├── Serial Port Management
│   ├── Port Detection
│   ├── Baud Rate Configuration
│   └── Connection State
├── Command Protocol
│   ├── Command Encoding
│   ├── Parameter Packing
│   └── Checksum Verification
├── Response Handling
│   ├── Message Parsing
│   ├── Status Interpretation
│   └── Error Detection
└── Device Interface
    ├── button Press Detection
    ├── Gantry Movement Status
    └── Servo State Feedback
```

## Command Protocol

### Message Format

```
[START_BYTE] [COMMAND] [PARAMETERS] [CHECKSUM] [END_BYTE]
0xAA         1 byte    variable     1 byte    0xFF
```

### Common Commands

- **HOME** - Move gantry to home position
- **MOVE** - Execute X,Y movement command
- **SERVO** - Control piece manipulation
- **STATUS** - Request device status
- **CALIBRATE** - Trigger calibration sequence

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
comm = Communication(port='/dev/ttyUSB0', baudrate=115200)

# Connect to device
comm.connect()

# Send command
comm.send_path(path_commands)

# Wait for button press (human move)
comm.wait_for_button_press()

# Disconnect
comm.disconnect()
```

## Error Handling

- **No Device Found** - Prompt user to connect device
- **Connection Lost** - Attempt automatic reconnection
- **Command Timeout** - Retry with backoff
- **Invalid Response** - Log error and request status
- **Checksum Failure** - Request retransmission

## Debugging

Enable debug logging to monitor communication:

```python
from Communication import Communication
import logging

logging.basicConfig(level=logging.DEBUG)

comm = Communication(port='/dev/ttyUSB0')
# All communication will be logged
```

## Dependencies

- `PySerial` - Serial port communication
- `USB libusb` - USB device interface
- Microcontroller firmware (ESP32/Arduino)
- Device drivers (OS-specific)
