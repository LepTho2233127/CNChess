
from time import time

import serial
import os
from Control import Command, Position


class Communication:
    SEND_COMMAND_TIMEOUT = 30  # Timeout for sending commands in seconds
    ser: serial.Serial
    def __init__(self):
        try:
            self.ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
        except Exception as e:
            print("Warning: could not open serial port /dev/ttyACM0:", e)
            self.ser = None
        # time.sleep(2) # attendre reset Arduino

    def send_command(self, command: Command):
        """
        Function responsible to send command object to esp-32. Command comes from get_path function that returns 
        chess board square and the magnet state (ex : MOVE 1 2 True)
        """

        if self.ser is None:
            print("Error: serial port not available")
            return False

        try:
            self.ser.write(f"CHESSMOVE|{command.position.x}|{command.position.y}|{int(command.magnet_state)};\n".encode('utf-8'))
        except Exception as e:
            print("Error writing to serial port:", e)
            return False

        if not self.validate_send_command():
            print("Error: Move command failed.")
            return False
        return True
    
    def send_path(self, path: list[Command]):
        """
        Function that sends a list of commands to ESP-32 via serial port
        """
        
        if self.ser is None:
            print("Error: serial port not available")
            return False

        try:
            self.ser.write(f"PATH".encode('utf-8'))
            for command in path:
                self.ser.write(f"|{command.position.x},{command.position.y},{int(command.magnet_state)}".encode('utf-8'))
            self.ser.write(";\n".encode('utf-8'))
        except Exception as e:
            print("Error writing to serial port:", e)
            return False

        if not self.validate_send_command():
            print("Error: Move command failed.")
            return False
        return True
    
    def send_position(self, pos:Position):
        """
        Function that sends a position to ESP-32 via serial port 
        ex: MOVE POSX POSY
        """
        
        try:
            self.ser.write(f"MOVE|{pos.x}|{pos.y};\n".encode('utf-8'))
        except Exception as e:
            print("Error writing to serial port:", e)
            return False
        
        if not self.validate_send_command(expected_responses=("DONE")):
            print("Error: Move command failed.")
            return False
        return True
    
    def validate_send_command(self, expected_responses=("DONE", "HOMED")) -> bool:
        """
        Wait for a line from serial and check whether it matches one of expected_responses.
        Returns True on match, False on timeout or unexpected response.
        """
        if self.ser is None:
            print("Error: serial port not available for validation")
            return False

        expected = set(expected_responses)
        start_time = time()

        while True:
            if time() - start_time > self.SEND_COMMAND_TIMEOUT:
                print("Error: No response from motor controller.")
                return False

            try:
                if self.ser.in_waiting == 0:
                    continue
                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
            except Exception as e:
                print("Error reading response from serial:", e)
                return False

            if not response:
                continue
            if response in expected:
                return True

            # PLAYED can arrive asynchronously while waiting for DONE/HOMED/STOPPED.
            if response == "PLAYED":
                continue

            print("Error: Unexpected response from motor controller:", response)
            return False

    def go_home(self):
        if self.ser is None:
            print("Error: serial port not available")
            return False

        try:
            self.ser.write("HOME;\n".encode('utf-8'))
        except Exception as e:
            print("Error writing HOME to serial:", e)
            return False

        # Expect the controller to reply with HOMED
        return self.validate_send_command(expected_responses=("HOMED",))
    

    
    def stop(self):
        "Send stop command to ESP-32"

        try:
            self.ser.write("STOP;\n".encode('utf-8'))
        except Exception as e:
            print("Error writing STOP to serial:", e)
            return False
        
        return self.validate_send_command(expected_responses=("STOPPED",))
    
    def move_servo(self, state: bool):
        "Send command to move servo to state (True for up, False for down)"

        try:
            self.ser.write(f"SERVO|{int(state)};\n".encode('utf-8'))
        except Exception as e:
            print("Error writing SERVO to serial:", e)
            return False
        
        return self.validate_send_command(expected_responses=("SERVO",))

    def wait_for_button_press(self):
        """
        Wait for a button press signal from ESP-32. This is used to detect when the user has placed a piece on the board.
        The ESP-32 should send "PLAYED" when a piece is placed.
        """
        if self.ser is None:
            print("Error: serial port not available")
            return False

        start_time = time()
        while True:
            if time() - start_time > 600:
                print("Error: No button press detected within timeout.")
                return False

            try:
                if self.ser.in_waiting == 0:
                    continue

                response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if not response:
                    continue
                if response == "PLAYED":
                    return True
            except Exception as e:
                print("Error reading serial in wait_for_button_press:", e)
                return False