"""File for the home page of the application, which is the first page that the user sees when they open the app. 
It contains buttons to choose difficulty, start a new game, and view settings """

import os
import sys
import chess
from PyQt6.QtWidgets import QWidget, QPushButton, QApplication
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6 import uic

# Ensure the parent package (python/) is on sys.path so CNChess can be imported
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from CNChess import CNChess

class HomeView(QWidget):

    def __init__(self, chess_model):
        
        super().__init__()
        self.chess_model = chess_model
        self.home_page_controller = HomePageController(chess_model)

        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'homePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        easy_button = self.findChild(QPushButton, "easyButton")
        medium_button = self.findChild(QPushButton, "intermediateButton")
        hard_button = self.findChild(QPushButton, "hardButton")
        white_button = self.findChild(QPushButton, "whiteButton")
        black_button = self.findChild(QPushButton, "blackButton")
        startButton = self.findChild(QPushButton, "startButton")

        easy_button.clicked.connect(self.home_page_controller.easy_button_clicked)
        medium_button.clicked.connect(self.home_page_controller.medium_button_clicked)
        hard_button.clicked.connect(self.home_page_controller.hard_button_clicked)
        white_button.clicked.connect(self.home_page_controller.white_button_clicked)
        black_button.clicked.connect(self.home_page_controller.black_button_clicked)
        startButton.clicked.connect(self.home_page_controller.start_game)

class HomePageController(QObject):
    # Define signals that will be emitted when user wants to navigate
    start_game_signal = pyqtSignal()

    def __init__(self, chess_model):
        super().__init__()
        self.chess_model = chess_model

    def easy_button_clicked(self):
        self.chess_model.set_difficulty("easy")

    def medium_button_clicked(self):
        self.chess_model.set_difficulty("medium")

    def hard_button_clicked(self):
        self.chess_model.set_difficulty("hard")    

    def white_button_clicked(self):
        self.chess_model.set_player_color(chess.WHITE)

    def black_button_clicked(self):
        self.chess_model.set_player_color(chess.BLACK)

    def start_game(self):
        # Emit the signal instead of directly calling a method
        self.start_game_signal.emit()    


if __name__ == "__main__":

    game = CNChess()
    controller = HomePageController(game)

    app = QApplication(sys.argv)
    home_view = HomeView(game, controller)
    home_view.show()
    sys.exit(app.exec())       