# This file contains the main logic to start the CNChess application and manage its components.
import sys
import chess
from PyQt6.QtWidgets import QApplication

from CNChess import CNChess
from Control import Control
from Cam import Cam
from Communication import Communication

from ui.main_ui import MainUI

if __name__ == "__main__":

    game = CNChess()
    game.reset_game()

    game.set_player_color(chess.WHITE)
    game.set_elo(2000)

    control = Control()
    control.update_board_state(game.get_board_state())

    cam = Cam(game, board_size=1200, camera_id=1)  # Adjust camera_id as needed
    cam.initialize_camera(calibrate=False)
    cam.process_image()  # Initial processing to set up the board state

    communication = Communication()
    # Create the Qt application
    app = QApplication(sys.argv) 
    
    ui = MainUI(game, control, communication, cam)
    
    # Show the window
    ui.show()
    
    # Run the application event loop
    sys.exit(app.exec())

    cam.release()
