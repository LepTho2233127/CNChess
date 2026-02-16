"""File containing the game page of the application, which is where the user plays the chess game. 
It contains the chess board, move history, and buttons to undo moves, resign, and start a new game. 
You can access th """

import os
import sys


from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6 import uic


class GameView(QWidget):
    
    def __init__(self, chess_model):
        
        super().__init__()
        self.chess_model = chess_model
        self.game_page_controller = GamePageController(chess_model)

        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'gamePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        settingsButton = self.findChild(QPushButton, "settingsButton")
        quitButton = self.findChild(QPushButton, "quitButton")  

        settingsButton.clicked.connect(self.game_page_controller.settings_button_clicked)     
        quitButton.clicked.connect(self.game_page_controller.quit_game)
          

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
    game_page_controller = GamePageController(chess_model)
    app = QApplication(sys.argv)
    game_view = GameView(chess_model, game_page_controller)
    game_view.show()
    sys.exit(app.exec())


