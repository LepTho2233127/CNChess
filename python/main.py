# This file contains the main logic to start the CNChess application and manage its components.
import sys
import chess
from PyQt6.QtWidgets import QApplication

from CNChess import CNChess
from Control import Control

from ui.chess_view import ChessView
from ui.chess_controller import ChessController

if __name__ == "__main__":

    game = CNChess()
    game.reset_game()

    game.set_player_color(chess.WHITE)
    game.set_elo(1320)

    control = Control()
    control.update_board_state(game.get_board_state())

      # Create the Qt application
    app = QApplication(sys.argv) 
    # Create view and controller
    view = ChessView(game)
    controller = ChessController(game, view)
    
    # Set the controller in the view
    view.controller = controller
    
    # Show the window
    view.show()
    
    # Run the application event loop
    sys.exit(app.exec())
