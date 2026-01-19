"""Chess Controller - Handles user interactions and updates model."""

from chess_model import ChessModel


class ChessController:
    """Controller for managing chess game logic and user interactions."""
    
    def __init__(self, model: ChessModel, view=None):
        """Initialize the controller with a model and optional view."""
        self.model = model
        self.view = view
    
    def set_view(self, view):
        """Set the view after initialization."""
        self.view = view
    
    def handle_square_click(self, row, col):
        """Handle a user click on a square."""
        selected = self.model.get_selected_piece()
        
        if selected is None:
            # No piece selected - select a piece if there is one
            self.model.select_piece(row, col)
        else:
            # A piece is already selected
            selected_row, selected_col = selected
            
            if (selected_row, selected_col) == (row, col):
                # Clicking the same square - deselect
                self.model.deselect_piece()
            else:
                # Try to move the piece
                piece = self.model.get_piece_at(selected_row, selected_col)
                if piece and piece != '_' and piece != '':
                    self.model.move_piece(selected_row, selected_col, row, col)
    
    def reset_board(self):
        """Reset the chess board to the starting position."""
        self.model.reset_board()
