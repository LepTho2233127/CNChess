"""File containing the game page of the application, which is where the user plays the chess game. 
It contains the chess board, move history, and buttons to undo moves, resign, and start a new game. 
You can access th """

import os
import sys

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6 import uic


class GameView(QWidget):

    LIGHT_SQUARE_COLOR = "#F0D9B5"
    DARK_SQUARE_COLOR = "#B58863"
    
    def __init__(self, chess_model):


        
        super().__init__()

        self.chess_model = chess_model
        self.game_page_controller = GamePageController(chess_model)
        self.images = self._load_piece_images()

        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'gamePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        settingsButton = self.findChild(QPushButton, "settingsButton")
        quitButton = self.findChild(QPushButton, "quitButton")  
        self.board = self.findChild(QGridLayout, "gridBoard")
        
        settingsButton.clicked.connect(self.game_page_controller.settings_button_clicked)     
        quitButton.clicked.connect(self.game_page_controller.quit_game)


        self.init_board(self.board)    

          

    def init_board(self, board_layout):
    
        for row in range(8):
            for col in range(8):
                square_color = (row + col) % 2
                square_button = QPushButton()
                square_button.setFixedSize(60, 60)  # Set a fixed size for the squares
                if square_color == 0:
                    square_button.setStyleSheet(f"background-color: {self.LIGHT_SQUARE_COLOR}; border: none;")
                else:
                    square_button.setStyleSheet(f"background-color: {self.DARK_SQUARE_COLOR}; border: none;")
                board_layout.addWidget(square_button, row, col)              

        board_layout.setSpacing(0)  # Remove spacing between squares
        board_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins around the board
        
    

    def _load_piece_images(self):
        """Load piece images from assets directory."""
        images = {}
        # Navigate up to python folder, then to chess_assets
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        assets_dir = os.path.join(assets_dir, 'chess_assets')

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

class GamePageController(QObject):
    # Define signals for navigation
    show_settings_signal = pyqtSignal()
    return_home_signal = pyqtSignal()

    def __init__(self, chess_model):
        super().__init__()
        self.chess_model = chess_model

    def settings_button_clicked(self):
        self.show_settings_signal.emit()

    def quit_game(self):
        self.return_home_signal.emit()


if __name__ == "__main__":

    # Ensure the parent package (python/) is on sys.path so CNChess can be imported
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    from CNChess import CNChess   

    chess_model = CNChess()
    app = QApplication(sys.argv)
    game_view = GameView(chess_model)
    game_view.show()
    sys.exit(app.exec())


