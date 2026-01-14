import chess
import stockfish
from chessboard import display

class CNChess:

    board: chess.Board
    computer_color: chess.Color
    player_color: chess.Color
    next_computer_move: chess.Move
    next_player_move: chess.Move

    stockfish_path: str = "/usr/games/stockfish"  # Adjust path as necessary
    stockfish_depth: int = 15
    computer: stockfish.Stockfish

    def __init__(self):
        self.board = chess.Board()
        self.computer_color = chess.BLACK
        self.player_color = chess.WHITE
        self.next_computer_move = None
        self.next_player_move = None
        self.computer = stockfish.Stockfish(path=self.stockfish_path, depth=self.stockfish_depth)
        self.game_visual = display.start()


    def set_elo(self, elo: int):
        self.computer.set_elo_rating(elo)

    def set_player_color(self, color: chess.Color):
        self.player_color = color
        self.computer_color = not color
    
    def get_player_color(self):
        return self.player_color

    def set_player_move(self, move):
        self.next_player_move = move
    
    def set_computer_move(self, move):
        self.next_computer_move = move
    
    def get_player_move(self):
        return self.next_player_move
    
    def get_computer_move(self):
        return self.next_computer_move
    
    def get_next_best_move(self):
        print("Calculating next best move...")
        self.computer.set_fen_position(self.board.fen())
        best_move_uci = self.computer.get_best_move()
        if best_move_uci:
            return chess.Move.from_uci(best_move_uci)
        else:
            return chess.Move.null()

    def make_move(self, move):
        print(f"Executing move: {move}")
        self.board.push(move)
    
    def get_board_state(self):
        return self.board.fen()

    def validate_move(self, move):
        return self.board.is_legal(move)
    
    def check_game_over(self):
        return self.board.is_game_over()
    
    def reset_game(self):
        print("Resetting the game...")
        self.board.reset()

    def get_turn(self):
        print("Current turn:", "White" if self.board.turn == chess.WHITE else "Black")
        return self.board.turn

    
    def display_board(self):
        display.update(self.get_board_state(), self.game_visual)