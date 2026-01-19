"""Chess Model - Manages the chess board state and game logic."""

from enum import Enum


class ChessPiece(Enum):
    """Chess piece enumeration."""
    WHITE_KING = 'K'
    WHITE_QUEEN = 'Q'
    WHITE_ROOK = 'R'
    WHITE_BISHOP = 'B'
    WHITE_KNIGHT = 'N'
    WHITE_PAWN = 'P'
    BLACK_KING = 'k'
    BLACK_QUEEN = 'q'
    BLACK_ROOK = 'r'
    BLACK_BISHOP = 'b'
    BLACK_KNIGHT = 'n'
    BLACK_PAWN = 'p'
    EMPTY = '_'


class ChessModel:
    """Model for managing chess board state."""
    
    def __init__(self):
        """Initialize chess board with default starting position."""
        self.board = self._create_default_board()
        self.selected_piece = None
        self.observers = []
    
    def _create_default_board(self):
        """Create and return the default chess starting position."""
        return [
            list('rnbqkbnr'),
            list('pppppppp'),
            list('________'),
            list('________'),
            list('________'),
            list('________'),
            list('PPPPPPPP'),
            list('RNBQKBNR'),
        ]
    
    def get_board(self):
        """Return the current board state."""
        return self.board
    
    def get_piece_at(self, row, col):
        """Get the piece at the specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None
    
    def set_piece_at(self, row, col, piece):
        """Set a piece at the specified position."""
        if 0 <= row < 8 and 0 <= col < 8:
            self.board[row][col] = piece
            self.notify_observers()
    
    def select_piece(self, row, col):
        """Select a piece at the given position."""
        if 0 <= row < 8 and 0 <= col < 8:
            if self.board[row][col] != '_' and self.board[row][col] != '':
                self.selected_piece = (row, col)
                self.notify_observers()
                return True
        return False
    
    def get_selected_piece(self):
        """Return the currently selected piece coordinates."""
        return self.selected_piece
    
    def move_piece(self, from_row, from_col, to_row, to_col):
        """Move a piece from one position to another."""
        if not (0 <= from_row < 8 and 0 <= from_col < 8 and 
                0 <= to_row < 8 and 0 <= to_col < 8):
            return False
        
        piece = self.board[from_row][from_col]
        if piece == '_' or piece == '':
            return False
        
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = '_'
        self.selected_piece = None
        self.notify_observers()
        return True
    
    def reset_board(self):
        """Reset the board to the starting position."""
        self.board = self._create_default_board()
        self.selected_piece = None
        self.notify_observers()
    
    def deselect_piece(self):
        """Deselect the currently selected piece."""
        self.selected_piece = None
        self.notify_observers()
    
    def attach_observer(self, observer):
        """Attach an observer to be notified of state changes."""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def detach_observer(self, observer):
        """Detach an observer."""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def notify_observers(self):
        """Notify all observers of state changes."""
        for observer in self.observers:
            observer.update()
