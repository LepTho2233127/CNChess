"""Chess View - PyQt-based UI for displaying the chess board."""

import os
import sys
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QFile
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont, QPen
from PyQt6 import uic
from Control import Position, Command

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class ChessBoardWidget(QWidget):
    """Custom widget for drawing the chess board and handling clicks."""
    
    piece_clicked = pyqtSignal(int, int)  # Signal emitted when a square is clicked
    
    # Board colors
    LIGHT_COLOR = QColor(240, 217, 181)
    DARK_COLOR = QColor(181, 136, 99)
    HIGHLIGHT_COLOR = QColor(100, 200, 150, 120)
    
    def __init__(self, cn_chess, parent=None):
        """Initialize the chess board widget."""
        super().__init__(parent)
        self.cn_chess = cn_chess
        self.selected_piece = None
        self.board_size = 640
        self.square_size = self.board_size // 8
        self.computer_turn = False
        self.trajectory = []
        
        # Load piece images
        self.piece_images = self._load_piece_images()
        
        # Set widget size
        self.setFixedSize(self.board_size, self.board_size)
        
    
    def _load_piece_images(self):
        """Load piece images from assets directory."""
        images = {}
        # Navigate up to python folder, then to chess_assets
        assets_dir = os.path.join(os.path.dirname(__file__), '..', 'chess_assets')
        
        piece_names = {
            'K': 'white-king', 'Q': 'white-queen', 'R': 'white-rook',
            'B': 'white-bishop', 'N': 'white-knight', 'P': 'white-pawn',
            'k': 'black-king', 'q': 'black-queen', 'r': 'black-rook',
            'b': 'black-bishop', 'n': 'black-knight', 'p': 'black-pawn',
        }
        
        # Try to load PNG images
        for piece_char, piece_name in piece_names.items():
            path = os.path.join(assets_dir, 'pieces_png', f'{piece_name}.png')
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    images[piece_char] = pixmap
        
        return images
    
    def _fen_to_board_array(self, fen: str):
        """Convert FEN string to 8x8 board array."""
        board_str = fen.split(' ')[0]
        rows = board_str.split('/')
        board = []
        
        for row in rows:
            board_row = []
            for char in row:
                if char.isdigit():
                    board_row.extend(['_'] * int(char))
                else:
                    board_row.append(char)
            board.append(board_row)
        
        return board
    
    def paintEvent(self, event):
        """Paint the chess board and pieces."""
        painter = QPainter(self)
        
        # Draw the board squares
        for row in range(8):
            for col in range(8):
                rect = self._get_square_rect(row, col)
                # Alternate colors
                if (row + col) % 2 == 0:
                    painter.fillRect(rect, self.LIGHT_COLOR)
                else:
                    painter.fillRect(rect, self.DARK_COLOR)
        
        # Draw pieces
        self._draw_pieces(painter)
        
        # Draw selection highlight
        self._draw_selection_highlight(painter)

        if self.computer_turn:
            self.draw_trajectory(self.trajectory, painter)
    
    def _get_square_rect(self, row, col):
        """Get the rectangle for a square at the given row and column."""
        x = col * self.square_size
        y = row * self.square_size
        return self.rect().adjusted(x, y, x - self.board_size + self.square_size, 
                                     y - self.board_size + self.square_size)
    
    def _draw_pieces(self, painter):
        """Draw all pieces on the board."""
        fen = self.cn_chess.get_board_state()
        board = self._fen_to_board_array(fen)
        for row in range(8):
            for col in range(8):
                piece = board[row][col]
                if piece != '_' and piece != '':
                    self._draw_piece(painter, row, col, piece)
    
    def _draw_piece(self, painter, row, col, piece):
        """Draw a single piece."""
        x = col * self.square_size
        y = row * self.square_size
        
        if piece in self.piece_images:
            pixmap = self.piece_images[piece]
            scaled_pixmap = pixmap.scaledToWidth(self.square_size, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(x, y, scaled_pixmap)
    
    def _draw_selection_highlight(self, painter):
        """Draw highlight on the selected piece."""
        if self.selected_piece:
            row, col = self.selected_piece
            x = col * self.square_size
            y = row * self.square_size
            painter.fillRect(x, y, self.square_size, self.square_size, self.HIGHLIGHT_COLOR)
    
    def mousePressEvent(self, event):
        """Handle mouse click events."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            col = pos.x() // self.square_size
            row = pos.y() // self.square_size
            
            if 0 <= row < 8 and 0 <= col < 8:
                self.piece_clicked.emit(row, col)
    
    def on_board_changed(self, selected_piece):
        """Called when board state changes."""
        self.selected_piece = selected_piece
        self.repaint()

    def draw_trajectory(self, trajectory, painter):
        """Draw trajectory on the board (not implemented)."""
        pen = QPen(QColor(255, 0, 0), 3, Qt.PenStyle.SolidLine)

        painter.setPen(pen)
        
        for i in range(len(trajectory) - 1):
            x1 = int(trajectory[i].position.x * self.square_size - self.square_size // 2)
            y1 = int((9 - trajectory[i].position.y) * self.square_size - self.square_size // 2)
            x2 = int(trajectory[i + 1].position.x * self.square_size - self.square_size // 2)
            y2 = int((9 - trajectory[i + 1].position.y) * self.square_size - self.square_size // 2)
            if trajectory[i].magnet_state:
                painter.drawLine(x1, y1, x2, y2)

    def set_computer_turn(self, is_computer_turn):
        """Set whether it's the computer's turn."""
        self.computer_turn = is_computer_turn

    def set_trajectory(self, trajectory):
        """Set the trajectory to be drawn."""
        self.trajectory = trajectory


class ChessView(QMainWindow):
    """Main window for the chess application."""
    
    def __init__(self, cn_chess, controller=None):
        """Initialize the main window from UI file."""
        super().__init__()
        self.cn_chess = cn_chess
        self.controller = controller
        
        # Load UI from .ui file
        ui_file_path = os.path.join(os.path.dirname(__file__), 'chess_main.ui')
        
        if not os.path.exists(ui_file_path):
            raise FileNotFoundError(f"Could not find UI file: {ui_file_path}")
        
        # Load the UI file using uic
        uic.loadUi(ui_file_path, self)
        
        # Set window properties
        self.setWindowTitle('CNChess - PyQt')
        self.setGeometry(100, 100, 740, 720)
        
        # Get widgets from loaded UI
        board_container = self.findChild(QWidget, 'boardContainer')
        self.status_label = self.findChild(QLabel, 'statusLabel')
        reset_button = self.findChild(QPushButton, 'resetButton')
        quit_button = self.findChild(QPushButton, 'quitButton')
        
        # Create chess board widget and add to container
        self.board_widget = ChessBoardWidget(cn_chess)
        
        # Replace the placeholder container with actual board widget
        if board_container and board_container.parent():
            layout = board_container.parent().layout()
            if layout:
                layout.replaceWidget(board_container, self.board_widget)
                board_container.deleteLater()
        
        # Connect signals
        self.board_widget.piece_clicked.connect(self.on_board_clicked)
        if reset_button:
            reset_button.clicked.connect(self.on_reset_clicked)
        if quit_button:
            quit_button.clicked.connect(self.close)
    
    def on_board_clicked(self, row, col):
        """Handle board click events."""
        if self.controller:
            self.controller.handle_square_click(row, col)
        self.update_status()
    
    def on_reset_clicked(self):
        """Handle reset button click."""
        if self.controller:
            self.controller.reset_board()
        self.update_status()
    
    def on_board_changed(self, selected_piece):
        """Called when board state changes from controller."""
        self.board_widget.on_board_changed(selected_piece)
        self.update_status()
    
    def update_status(self):
        """Update the status label."""
        status_text = "Ready"
        
        # Add turn indicator
        try:
            turn = self.cn_chess.get_turn()
            turn_text = "White's turn" if turn else "Black's turn"
            status_text = turn_text
        except Exception:
            pass
        
        # Add selection info if piece is selected
        if self.board_widget.selected_piece:
            row, col = self.board_widget.selected_piece
            status_text += f" | Selected: ({row}, {col})"
        
        # Add game over indicator
        try:
            if self.cn_chess.check_game_over():
                status_text += " | Game Over"
        except Exception:
            pass
        
        self.status_label.setText(status_text)
