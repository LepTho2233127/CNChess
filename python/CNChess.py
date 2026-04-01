import chess
import random
import stockfish

from chess import Termination

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
        """Initialize CNChess game instance with board, colors, and difficulty settings.
        
        Args:
            None
        
        Return:
            None
        """
        self.board = chess.Board()
        self.computer_color = chess.BLACK
        self.player_color = chess.WHITE
        self.next_computer_move = None
        self.next_player_move = None
        self.computer = stockfish.Stockfish(path=self.stockfish_path, depth=self.stockfish_depth)
        self.MEDIUM_ELO = 1350
        self.MEDIUM_DEPTH = 1
        self.HARD_ELO = 2000
        self.HARD_DEPTH = 10
        self.IMPOSSIBLE_ELO = 3000
        self.IMPOSSIBLE_DEPTH = 20
        self.difficulty = "easy"


    def set_elo(self, elo: int):
        """Set ELO rating for computer opponent.
        
        Args:
            elo (int): ELO rating value.
        
        Return:
            None
        """
        self.computer.set_elo_rating(elo)

    def set_depth(self, depth: int):
        """Set search depth for computer AI engine.
        
        Args:
            depth (int): Search depth value.
        
        Return:
            None
        """
        self.computer.set_depth(depth)

    def set_difficulty(self, difficulty: str):
        """Set the difficulty level of the computer opponent. Valid values are 'easy', 'medium', and 'hard'."""

        if difficulty not in ["easy", "medium", "hard", "impossible"]:
            raise ValueError("Invalid difficulty level. Must be 'easy', 'medium', 'hard', or 'impossible'.")
        self.difficulty = difficulty
        elo = self.MEDIUM_ELO if difficulty == "medium" else self.HARD_ELO if difficulty == "hard" else self.IMPOSSIBLE_ELO
        depth = self.MEDIUM_DEPTH if difficulty == "medium" else self.HARD_DEPTH if difficulty == "hard" else self.IMPOSSIBLE_DEPTH

        self.set_elo(elo)
        self.set_depth(depth)

    def set_player_color(self, color: chess.Color):
        """Set player color (WHITE/BLACK) and computer color as opposite.
        
        Args:
            color (chess.Color): Player's color (chess.WHITE or chess.BLACK).
        
        Return:
            None
        """
        self.player_color = color
        self.computer_color = not color
    
    def get_player_color(self):
        """Return the player's color.
        
        Args:
            None
        
        Return:
            chess.Color: Player's color (chess.WHITE or chess.BLACK).
        """
        return self.player_color

    def get_legal_moves_from_square(self, square):
        """Return list of legal moves from a given square.
        
        Args:
            square (str): Square in algebraic notation (e.g., 'e2').
        
        Return:
            list[chess.Move]: List of legal moves from the specified square.
        """
        square_index = chess.parse_square(square)
        legal_moves = [move for move in self.board.legal_moves if move.from_square == square_index]
        return legal_moves
     
    def set_player_move(self, move):
        """Store the next player move to be executed.
        
        Args:
            move (chess.Move): The move to store.
        
        Return:
            None
        """
        self.next_player_move = move
    
    def set_computer_move(self, move):
        """Store the next computer move to be executed.
        
        Args:
            move (chess.Move): The move to store.
        
        Return:
            None
        """
        self.next_computer_move = move
    
    def get_player_move(self):
        """Return stored player move.
        
        Args:
            None
        
        Return:
            chess.Move: Stored player move.
        """
        return self.next_player_move
    
    def get_computer_move(self):
        """Return stored computer move.
        
        Args:
            None
        
        Return:
            chess.Move: Stored computer move.
        """
        return self.next_computer_move
    
    def get_next_best_move(self):
        """Calculate and return the best move for computer based on difficulty level.
        
        Args:
            None
        
        Return:
            chess.Move: Best move for computer, or null move if none available.
        """
        self.computer.set_fen_position(self.board.fen())
        if self.difficulty == "easy":
            captured_moves = list(self.board.generate_legal_captures())
            if captured_moves:
                move = captured_moves[random.randrange(len(captured_moves))]
            else:
                legal_moves = list(self.board.generate_legal_moves())
                move = legal_moves[random.randrange(len(legal_moves))]
            return move
        else:
            best_move_uci = self.computer.get_best_move()
        if best_move_uci:
            return chess.Move.from_uci(best_move_uci)
        else:
            return chess.Move.null()    
        
    def check_game_outcome(self):
        """Check if game is over and return winner or draw status.
        
        Args:
            None
        
        Return:
            str: "white" or "black" for winner, "draw" for draw, None if game ongoing.
        """
        game_outcome = self.board.outcome()
        if game_outcome:
            if game_outcome.termination == Termination.CHECKMATE:
                winner_color = "white" if game_outcome.winner == chess.WHITE else "black"
                return winner_color
            else:
                return "draw"
        else:
            return None 
    def get_material_evaluation(self, color):
        """Calculate material score for a given color based on pieces on board.
        
        Args:
            color (chess.Color): Color to evaluate (chess.WHITE or chess.BLACK).
        
        Return:
            int: Material evaluation score.
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }
        evaluation = 0
        for piece, value in piece_values.items():
            pieces = self.board.pieces(piece, color)
            evaluation += len(pieces) * value
        return evaluation      

    def make_move(self, move):
        """Execute a move on the board.
        
        Args:
            move (chess.Move): Move to execute.
        
        Return:
            None
        """
        self.board.push(move)    
    
    def get_board_state(self):
        """Return FEN string representation of current board state.
        
        Args:
            None
        
        Return:
            str: FEN notation of board state.
        """
        return self.board.fen()

    def validate_move(self, move):
        """Check if a move is legal in current board position.
        
        Args:
            move (chess.Move): Move to validate.
        
        Return:
            bool: True if move is legal, False otherwise.
        """
        return self.board.is_legal(move)
    
    def check_game_over(self):
        """Check if game is over (checkmate, stalemate, or insufficient material).
        
        Args:
            None
        
        Return:
            bool: True if game is over, False otherwise.
        """
        return self.board.is_game_over()
    
    def reset_game(self):
        """Reset board to starting position.
        
        Args:
            None
        
        Return:
            None
        """
        print("Resetting the game...")
        self.board.reset()

    def get_turn(self):
        """Return whose turn it is to move.
        
        Args:
            None
        
        Return:
            str: "white" or "black" indicating current turn.
        """
        turn = self.board.turn
        return "white" if turn == chess.WHITE else "black"
    
    def get_board(self):
        """Return the chess.Board object.
        
        Args:
            None
        
        Return:
            chess.Board: Current chess board instance.
        """
        return self.board
    
    def is_promotion_move(self, move):
        """Determine if a move is a pawn promotion.
        
        Args:
            move (chess.Move): Move to check.
        
        Return:
            bool: True if move is a pawn promotion, False otherwise.
        """
        white_promotion = (chess.square_rank(move.to_square) == 7 and
                          chess.square_rank(move.from_square) == 6 and
                          self.board.piece_at(move.from_square).piece_type == chess.PAWN and
                          self.board.piece_at(move.from_square).color == chess.WHITE)
        black_promotion = (chess.square_rank(move.to_square) == 0 and
                          chess.square_rank(move.from_square) == 1 and
                          self.board.piece_at(move.from_square).piece_type == chess.PAWN and
                          self.board.piece_at(move.from_square).color == chess.BLACK)
        return white_promotion or black_promotion            

    