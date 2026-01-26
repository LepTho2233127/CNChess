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

    while not game.check_game_over():
        # Here you would normally get the player's move from input
        path = []
        if game.get_turn()== game.get_player_color():
            player_move = game.get_next_best_move()  # Placeholder for actual player move
            if game.validate_move(player_move):
                game.set_player_move(player_move)
                control.update_board_state(game.get_board_state())
                game.make_move(game.get_player_move())
            else: 
                print("Invalid move by player.")
        else:
            game.set_computer_move(game.get_next_best_move())
            game.make_move(game.get_computer_move())
            control.update_board_state(game.get_board_state())
            path = control.get_path(game.get_computer_move())
            control.print_path(path)
            traj = control.calculate_trajectory(path)
            control.print_trajectory(traj)
        
        game.display_board()

    game.display_board()
    print("Game over!")
    wait = input("Press Enter to exit...")
