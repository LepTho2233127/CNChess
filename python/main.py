# This file contains the mane logic to start the CNChess application and manage its components.
import chess
from CNChess import CNChess


if __name__ == "__main__":
    game = CNChess()
    game.reset_game()

    game.set_player_color(chess.WHITE)
    game.set_elo(1320)

    while not game.check_game_over():
        # Here you would normally get the player's move from input
        if game.get_turn()== game.get_player_color():
            player_move = game.get_next_best_move()  # Placeholder for actual player move
            if game.validate_move(player_move):
                game.set_player_move(player_move)
                game.make_move(game.get_player_move())
            else: 
                print("Invalid move by player.")
        else:
            game.set_computer_move(game.get_next_best_move())
            game.make_move(game.get_computer_move())
        
        game.display_board()