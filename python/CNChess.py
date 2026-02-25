import chess
import stockfish

class CNChess:

    board: chess.Board
    computer_color: chess.Color
    player_color: chess.Color
    next_computer_move: chess.Move
    next_player_move: chess.Move

    stockfish_path: str = "/usr/games/stockfish"  # Adjust path as necessary
    stockfish_depth: int = 10
    computer: stockfish.Stockfish

    def __init__(self):
        self.board = chess.Board()
        self.computer_color = chess.BLACK
        self.player_color = chess.WHITE
        self.next_computer_move = None
        self.next_player_move = None
        self.computer = stockfish.Stockfish(path=self.stockfish_path, depth=self.stockfish_depth)
        self.EASY_ELO = 1350
        self.EASY_DEPTH = 1
        self.MEDIUM_ELO = 1350
        self.MEDIUM_DEPTH = 5
        self.HARD_ELO = 2000
        self.HARD_DEPTH = 10
        self.IMPOSSIBLE_ELO = 3000
        self.IMPOSSIBLE_DEPTH = 20
        self.difficulty = "medium"


    def set_elo(self, elo: int):
        self.computer.set_elo_rating(elo)

    def set_depth(self, depth: int):
        self.computer.set_depth(depth)

    def set_difficulty(self, difficulty: str):
        """Set the difficulty level of the computer opponent. Valid values are 'easy', 'medium', and 'hard'."""

        if difficulty not in ["easy", "medium", "hard", "impossible"]:
            raise ValueError("Invalid difficulty level. Must be 'easy', 'medium', 'hard', or 'impossible'.")
        self.difficulty = difficulty
        elo = self.EASY_ELO if difficulty == "easy" else self.MEDIUM_ELO if difficulty == "medium" else self.HARD_ELO if difficulty == "hard" else self.IMPOSSIBLE_ELO
        depth = self.EASY_DEPTH if difficulty == "easy" else self.MEDIUM_DEPTH if difficulty == "medium" else self.HARD_DEPTH if difficulty == "hard" else self.IMPOSSIBLE_DEPTH

        self.set_elo(elo)
        self.set_depth(depth)

    def set_player_color(self, color: chess.Color):
        self.player_color = color
        self.computer_color = not color
    
    def get_player_color(self):
        return self.player_color


    def get_legal_moves_from_square(self, square):
        
        square_index = chess.parse_square(square)
        legal_moves = [move for move in self.board.legal_moves if move.from_square == square_index]

        return legal_moves
     
    def set_player_move(self, move):
        self.next_player_move = move
    
    def set_computer_move(self, move):
        self.next_computer_move = move
    
    def get_player_move(self):
        return self.next_player_move
    
    def get_computer_move(self):
        return self.next_computer_move
    
    def get_next_best_move(self):
        self.computer.set_fen_position(self.board.fen())
        if self.difficulty == "easy":
            top_moves = self.computer.get_top_moves(5)
            best_move_uci = top_moves[4]['Move'] if top_moves else None
        else:
            best_move_uci = self.computer.get_best_move()
        if best_move_uci:
            return chess.Move.from_uci(best_move_uci)
        else:
            return chess.Move.null()    

    def make_move(self, move):
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
        return self.board.turn
    
    def get_board(self):
        return self.board
    

    