"""Chess View - PyQt-based UI for displaying the chess board."""

import os
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QFile
from PyQt6.QtGui import QPainter, QColor, QPixmap, QFont
from PyQt6 import uic
from chess_model import ChessModel


class ChessBoardWidget(QWidget):
    """Custom widget for drawing the chess board and handling clicks."""
    
    piece_clicked = pyqtSignal(int, int)  # Signal emitted when a square is clicked
    
    # Board colors
    LIGHT_COLOR = QColor(240, 217, 181)
    DARK_COLOR = QColor(181, 136, 99)
    HIGHLIGHT_COLOR = QColor(100, 200, 150, 120)
    
    def __init__(self, model: ChessModel, parent=None):
        """Initialize the chess board widget."""
        super().__init__(parent)
        self.model = model
        self.board_size = 640
        self.square_size = self.board_size // 8
        
        # Load piece images
        self.piece_images = self._load_piece_images()
        
        # Set widget size
        self.setFixedSize(self.board_size, self.board_size)
        
        # Attach this view as an observer to the model
        self.model.attach_observer(self)
    
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
    
    def _get_square_rect(self, row, col):
        """Get the rectangle for a square at the given row and column."""
        x = col * self.square_size
        y = row * self.square_size
        return self.rect().adjusted(x, y, x - self.board_size + self.square_size, 
                                     y - self.board_size + self.square_size)
    
    def _draw_pieces(self, painter):
        """Draw all pieces on the board."""
        board = self.model.get_board()
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
        selected = self.model.get_selected_piece()
        if selected:
            row, col = selected
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
    
    def update(self):
        """Called by model observer pattern when model changes."""
        self.repaint()


class ChessView(QMainWindow):
    """Main window for the chess application."""
    
    def __init__(self, model: ChessModel, controller=None):
        """Initialize the main window from UI file."""
        super().__init__()
        self.model = model
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
        self.board_widget = ChessBoardWidget(model)
        
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
        
        # Attach model observer
        model.attach_observer(self)
    
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
    
    def update_status(self):
        """Update the status label."""
        selected = self.model.get_selected_piece()
        if selected:
            row, col = selected
            self.status_label.setText(f'Selected: ({row}, {col})')
        else:
            self.status_label.setText('Ready')
    
    def update(self):
        """Called by model observer pattern when model changes."""
        self.update_status()
        self.board_widget.update()
