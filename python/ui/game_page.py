"""File containing the game page of the application, which is where the user plays the chess game. 
It contains the chess board, move history, and buttons to undo moves, resign, and start a new game. 
You can access th """

import os
import sys

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QApplication, QSizePolicy
from PyQt6.QtCore import QObject, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6 import uic


LIGHT_SQUARE_COLOR = "#F0D9B5"
DARK_SQUARE_COLOR = "#B58863"
    
class GameView(QWidget):

  
    def __init__(self, chess_game):

        super().__init__()

        self.chess_game = chess_game
        self.game_page_controller = GamePageController(chess_game)
       

        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'gamePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        settings_button = self.findChild(QPushButton, "settingsButton")
        quit_button = self.findChild(QPushButton, "quitButton")  
        board_layout = self.findChild(QVBoxLayout, "rightLayout")

        board_layout.removeItem(board_layout.itemAt(1))  
        board = AspectRatioWidget(ChessBoardWidget(chess_game))
        board_layout.insertWidget(1,board)


        settings_button.clicked.connect(self.game_page_controller.settings_button_clicked)     
        quit_button.clicked.connect(self.game_page_controller.quit_game)

  
    
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

class ChessBoardWidget(QWidget):
    def __init__(self, chess_game):
        super().__init__()

        self.images = self._load_piece_images()
        self.chess_game = chess_game
        self.board = self.fen_to_board_array(self.chess_game.get_board_state())
        self.board_layout = self.init_board()
        self.setLayout(self.board_layout)
            
    def init_board(self):

        board_layout = QGridLayout()

        for row in range(8):
            for col in range(8):
                square_color = (row + col) % 2
                square_button = GridButton()
                square_button.setMinimumSize(60, 60)  # Set a minimum size for the squares
                square_button.resize()  # Set a base size for the squares to maintain aspect ratio
                if square_color == 0:
                    square_button.setStyleSheet(f"background-color: {LIGHT_SQUARE_COLOR}; border: none;")
                else:
                    square_button.setStyleSheet(f"background-color: {DARK_SQUARE_COLOR}; border: none;")

                board_layout.addWidget(square_button, row, col)
                self.draw_piece(square_button, self.board[row][col])  # Initialize with empty squares

        for i in range(8):
            board_layout.setRowStretch(i, 1)  # Make rows stretchable
            board_layout.setColumnStretch(i, 1)  # Make columns stretchable        

        board_layout.setSpacing(0)
        board_layout.setVerticalSpacing(0)  # Remove spacing between squares

        return board_layout
    
    def _load_piece_images(self):
        """Load piece images from assets directory."""
        images = {}
        # Navigate up to python folder, then to chess_assets
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets','chess_assets')

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
                icon = QIcon(path)
                if not icon.isNull():
                    images[piece_char] = icon
        
        return images  
    
    def update_board(self, board_state):
        """Update the board display based on the new board state (FEN string)."""
        self.board = self.fen_to_board_array(board_state)
        for row in range(8):
            for col in range(8):
                square_button = self.board_layout.itemAtPosition(row, col).widget()
                piece_char = self.board[row][col]
                self.draw_piece(square_button, piece_char)
    
    def draw_piece(self, button, piece_char):
        """Draw the piece on the given square button."""
        
        if piece_char in self.images:
            icon = self.images[piece_char]
            button.setIcon(icon)
            button.setIconSize(button.size())

    def fen_to_board_array(self, fen: str):
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
        
    
class AspectRatioWidget(QWidget):
    
    def __init__(self, board_widget, parent=None):
        super().__init__(parent)
        self.board_widget = board_widget
        self.board_widget.setParent(self) # Make the board a child of this container

    def resizeEvent(self, event):
     
        w = event.size().width()
        h = event.size().height()

        side = min(w, h)

        x = (w - side) // 2
        y = (h - side) // 2

        self.board_widget.setGeometry(x, y, side, side)    
        self.board_widget.update_board(self.board_widget.chess_game.get_board_state())  # Update the board display on resize

 
class GridButton(QPushButton):
    def __init__(self):
        super().__init__()

        sizePolicy = self.sizePolicy()
        sizePolicy.setHeightForWidth(True)
        self.setSizePolicy(sizePolicy)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


    def heightForWidth(self, width):
        return width  
             

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


