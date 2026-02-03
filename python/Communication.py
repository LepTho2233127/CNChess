
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
            self.ser.write(f"CHESSMOVE {command.position.x} {command.position.y} {command.magnet_state} \n".encode('utf-8'))
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
            self.ser.write(f"MOVE {pos.x} {pos.y} \n".encode('utf-8'))
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

        start_time = time()
        # Wait for data or timeout
        while True:
            try:
                if self.ser.in_waiting > 0:
                    break
            except Exception as e:
                print("Error reading serial in_waiting:", e)
                return False

            if time() - start_time > self.SEND_COMMAND_TIMEOUT:
                print("Error: No response from motor controller.")
                return False

        try:
            response = self.ser.readline().decode('utf-8').strip()
        except Exception as e:
            print("Error reading response from serial:", e)
            return False

        if response in expected_responses:
            return True
        else:
            print("Error: Unexpected response from motor controller:", response)
            return False

    def goHome(self):
        if self.ser is None:
            print("Error: serial port not available")
            return False

        try:
            self.ser.write("HOME\n".encode('utf-8'))
        except Exception as e:
            print("Error writing HOME to serial:", e)
            return False

        # Expect the controller to reply with HOMED
        return self.validate_send_command(expected_responses=("HOMED",))
    

    
    def stop(self):
        "Send stop command to ESP-32"

        try:
            self.ser.write("HOME\n".encode('utf-8'))
        except Exception as e:
            print("Error writing HOME to serial:", e)
            return False
        
        return self.validate_send_command(expected_responses=("STOPPED"))
        


        