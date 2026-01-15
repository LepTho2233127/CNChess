# This file contains the main logic to start the CNChess application and manage its components.
import chess
from CNChess import CNChess
from Control import Control


if __name__ == "__main__":
    game = CNChess()
    game.reset_game()

    game.set_player_color(chess.WHITE)
    game.set_elo(1320)

    control = Control()
    control.update_board_state(game.get_board_state())

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
            path = control.move_piece(game.get_computer_move())
            control.print_path(path)

        
        game.display_board()
        control.grid.print_grid()

    game.display_board()
    print("Game over!")
    wait = input("Press Enter to exit...")
