"""File for the home page of the application, which is the first page that the user sees when they open the app. 
It contains buttons to choose difficulty, start a new game, and view settings """

import os
import sys
import chess
from PyQt6.QtWidgets import QWidget, QPushButton, QApplication
from PyQt6 import uic
from CNChess import CNChess

class HomeView(QWidget):

    def __init__(self, chess_model, home_page_controller):
        
        super().__init__()
        self.chess_model = chess_model
        self.home_page_controller = home_page_controller

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

        easy_button.clicked.connect(self.home_page_controller.easy_button_clicked)
        medium_button.clicked.connect(self.home_page_controller.medium_button_clicked)
        hard_button.clicked.connect(self.home_page_controller.hard_button_clicked)
        white_button.clicked.connect(self.home_page_controller.white_button_clicked)
        black_button.clicked.connect(self.home_page_controller.black_button_clicked)

        
class HomePageController:

    def __init__(self, chess_model):
        self.chess_model = chess_model

    def easy_button_clicked(self):
        self.chess_model.set_difficulty("easy")
        print("Easy button clicked")

    def medium_button_clicked(self):
        self.chess_model.set_difficulty("medium")
        print("Medium button clicked")

    def hard_button_clicked(self):
        self.chess_model.set_difficulty("hard")    
        print("Hard button clicked")       

    def white_button_clicked(self):
        self.chess_model.set_player_color(chess.WHITE)
        print("White button clicked")

    def black_button_clicked(self):
        self.chess_model.set_player_color(chess.BLACK)
        print("Black button clicked")                                                

if __name__ == "__main__":

    game = CNChess()
    controller = HomePageController(CNChess.CNChess())

    app = QApplication(sys.argv)
    home_view = HomeView(game, controller)
    home_view.show()
    sys.exit(app.exec())       