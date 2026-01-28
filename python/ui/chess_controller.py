"""Chess Controller - Handles user interactions with CNChess."""

import chess
from Control import Control, Communication
from PyQt6.QtCore import QTimer


class ChessController:
    """Controller for managing chess game logic and user interactions."""
    
    def __init__(self, cn_chess, view=None):
        """Initialize the controller with CNChess instance and optional view."""
        self.cn_chess = cn_chess
        self.view = view
        self.selected_piece = None
        self.computer_timer = QTimer()
        self.computer_timer.timeout.connect(self.handle_computer_move)
        self.cn_chess.set_player_color(chess.WHITE)
        self.control = Control()
        self.control.update_board_state(self.cn_chess.get_board_state())
        self.communication = Communication()
    def set_view(self, view):
        """Set the view after initialization."""
        self.view = view
    
    def handle_square_click(self, row, col):
        """Handle a user click on a square."""
        if self.selected_piece is None:
            # No piece selected - select a piece if there is one
            piece = self._get_piece_at(row, col)
            if piece != '_' and piece != '':
                self.selected_piece = (row, col)
                self._update_view()
        else:
            # A piece is already selected
            selected_row, selected_col = self.selected_piece
            
            if (selected_row, selected_col) == (row, col):
                # Clicking the same square - deselect
                self.selected_piece = None
                self._update_view()
            else:
                # Try to move the piece
                if self._try_move_piece(selected_row, selected_col, row, col):
                    self.selected_piece = None
                    self._update_view()
                else:
                    # Move was invalid, try selecting the new piece instead
                    piece = self._get_piece_at(row, col)
                    if piece != '_' and piece != '':
                        self.selected_piece = (row, col)
                    else:
                        self.selected_piece = None
                    self._update_view()
    
    def reset_board(self):
        """Reset the chess board to the starting position."""
        self.cn_chess.reset_game()
        self.selected_piece = None
        self._update_view()
    
    def _get_piece_at(self, row, col):
        """Get piece at position from board state."""
        if 0 <= row < 8 and 0 <= col < 8:
            fen = self.cn_chess.get_board_state()
            board_str = fen.split(' ')[0]
            rows = board_str.split('/')
            board_row = rows[row]
            
            col_index = 0
            for char in board_row:
                if char.isdigit():
                    col_index += int(char)
                else:
                    if col_index == col:
                        return char
                    col_index += 1
            return '_'
        return None
    
    def _try_move_piece(self, from_row, from_col, to_row, to_col):
        """Try to move piece and return whether move was successful."""
        if not (0 <= from_row < 8 and 0 <= from_col < 8 and 
                0 <= to_row < 8 and 0 <= to_col < 8):
            return False
        
        # Convert to chess notation (columns: a-h, rows: 1-8)
        from_square = chess.square(from_col, 7 - from_row)
        to_square = chess.square(to_col, 7 - to_row)
        
        try:
            
            move = chess.Move(from_square, to_square)
            
            # Validate move with promotion if needed
            if self.cn_chess.validate_move(move):
                self.cn_chess.make_move(move)
                if self.cn_chess.get_turn() == self.cn_chess.computer_color:
                    self.computer_timer.start(1000)
                return True
            else:
                # Try as promotion move for pawns
                for promotion in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                    move = chess.Move(from_square, to_square, promotion=promotion)
                    if self.cn_chess.validate_move(move):
                        self.cn_chess.make_move(move)
                        return True
        except Exception:
            pass
        
        self.control.update_board_state(self.cn_chess.get_board_state())

        return False
    
    
    def _update_view(self):
        """Update the view with current board state."""
        if self.view:
            self.view.on_board_changed(self.selected_piece)

    def handle_computer_move(self):
        """Handle the computer's move."""
        self.computer_timer.stop()

        if self.cn_chess.check_game_over():
            return

        # Get computer's best move
        computer_move = self.cn_chess.get_next_best_move()

        if computer_move and self.cn_chess.validate_move(computer_move):
            self.control.update_board_state(self.cn_chess.get_board_state())
            path = self.control.get_path(computer_move)
            trajectory = self.control.calculate_trajectory(path)
            self.communication.send_command(trajectory)

            self.control.print_path(path)
            self.cn_chess.make_move(computer_move)
            self.view.board_widget.set_trajectory(path)
            self.view.board_widget.set_computer_turn(True)
            # Update the view
            self._update_view()
            self.view.board_widget.set_computer_turn(False)
            
            # Check if now it's player's turn again
            if self.cn_chess.get_turn() == self.cn_chess.player_color:
                self.selected_piece = None