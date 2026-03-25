"""File for the home page of the application, which is the first page that the user sees when they open the app. 
It contains buttons to choose difficulty, start a new game, and view settings """

import os
import sys
import chess
from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QObject, QSize, Qt, pyqtSignal
from PyQt6 import uic

# Ensure the parent package (python/) is on sys.path so CNChess can be imported
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# from CNChess import CNChess

class HomeView(QWidget):

    def __init__(self, chess_model):
        
        super().__init__()
        self.chess_model = chess_model
        self.home_page_controller = HomePageController(chess_model)
        self.init_ui()
    
    def init_ui(self):

        logo_label = QLabel(self)
        logo_pixmap = QPixmap(os.path.join(os.path.dirname(__file__), "assets/logo_pixel.png"))
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(800, 400, Qt.AspectRatioMode.KeepAspectRatio)
        logo_label.setPixmap(logo_pixmap)

        level_layout = self.build_level_buttons()
        color_layout = self.build_color_buttons()
        menu_layout = self.build_menu_buttons()
        

        hbox_layout = QHBoxLayout()
        hbox_layout.addStretch(20)
        hbox_layout.addLayout(color_layout)
        hbox_layout.addSpacing(50)
        hbox_layout.addLayout(menu_layout)
        hbox_layout.addStretch(20)

        main_layout = QVBoxLayout()
        main_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addSpacing(20)
        main_layout.addLayout(level_layout)
        main_layout.addSpacing(20)
        main_layout.addLayout(hbox_layout)
        self.setLayout(main_layout)

        # Load the UI from the .ui file
        # ui_path = os.path.join(os.path.dirname(__file__), 'homePage.ui')

        # if not os.path.exists(ui_path):
        #     raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        # uic.loadUi(ui_path, self)

        # easy_button = self.findChild(QPushButton, "easyButton")
        # medium_button = self.findChild(QPushButton, "intermediateButton")
        # hard_button = self.findChild(QPushButton, "hardButton")
        # white_button = self.findChild(QPushButton, "whiteButton")
        # black_button = self.findChild(QPushButton, "blackButton")
        # startButton = self.findChild(QPushButton, "startButton")

    def build_level_buttons(self):
        
        level_button_size = QSize(175, 175)

        easy_button = QPushButton(self)
        easy_path = os.path.join(os.path.dirname(__file__), "assets", "beginner_icon.png")
        easy_pixmap = QPixmap(easy_path)
        easy_icon = QIcon(easy_pixmap)
        easy_button.setIcon(easy_icon)
        easy_button.setIconSize(level_button_size)
        easy_button.setFixedSize(level_button_size)
        medium_button = QPushButton(self)
        medium_path = os.path.join(os.path.dirname(__file__), "assets", "intermediate_icon.png")
        medium_pixmap = QPixmap(medium_path)
        medium_icon = QIcon(medium_pixmap)
        medium_button.setIcon(medium_icon)
        medium_button.setIconSize(level_button_size)
        medium_button.setFixedSize(level_button_size)
        hard_button = QPushButton(self)
        hard_path = os.path.join(os.path.dirname(__file__), "assets", "expert_icon.png")
        hard_pixmap = QPixmap(hard_path)
        hard_icon = QIcon(hard_pixmap)
        hard_button.setIcon(hard_icon)
        hard_button.setIconSize(level_button_size)
        hard_button.setFixedSize(level_button_size)

        easy_button.clicked.connect(self.home_page_controller.easy_button_clicked)
        medium_button.clicked.connect(self.home_page_controller.medium_button_clicked)
        hard_button.clicked.connect(self.home_page_controller.hard_button_clicked)

        layout = QHBoxLayout()
        layout.addStretch(50)
        layout.addWidget(easy_button)
        layout.addWidget(medium_button)
        layout.addWidget(hard_button)
        layout.addStretch(50)

        return layout
    
    def build_color_buttons(self):

        color_button_size = QSize(100, 100)

        white_button = QPushButton(self)
        white_path = os.path.join(os.path.dirname(__file__), "assets", "chess_assets", "pieces_png", "white-pawn.png")
        white_pixmap = QPixmap(white_path)
        white_icon = QIcon(white_pixmap)
        white_button.setIcon(white_icon)
        white_button.setIconSize(color_button_size)
        white_button.setFixedSize(color_button_size)
        black_button = QPushButton(self)
        black_path = os.path.join(os.path.dirname(__file__), "assets", "chess_assets", "pieces_png", "black-pawn.png")
        black_pixmap = QPixmap(black_path)
        black_icon = QIcon(black_pixmap)
        black_button.setIcon(black_icon)
        black_button.setIconSize(color_button_size)
        black_button.setFixedSize(color_button_size)

        white_button.clicked.connect(self.home_page_controller.white_button_clicked)
        black_button.clicked.connect(self.home_page_controller.black_button_clicked)

        layout = QHBoxLayout()
        layout.addWidget(white_button)
        layout.addWidget(black_button)

        return layout
    
    def build_menu_buttons(self):

        start_button = QPushButton("START GAME", self)
        start_button.clicked.connect(self.home_page_controller.start_game)
        start_button.setObjectName("menu_button")

        settings_button = QPushButton("SETTINGS", self)
        settings_button.clicked.connect(self.home_page_controller.settings_button_clicked)
        settings_button.setObjectName("menu_button")

        layout = QVBoxLayout()
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        return layout

class HomePageController(QObject):
    # Define signals that will be emitted when user wants to navigate
    start_game_signal = pyqtSignal()
    settings_signal = pyqtSignal()

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
    
    def settings_button_clicked(self):
        self.settings_signal.emit()

if __name__ == "__main__":

    # game = CNChess()
    controller = HomePageController(None)

    app = QApplication(sys.argv)
    qss_path = os.path.join(os.path.dirname(__file__), "cnchess_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: QSS theme file not found at {qss_path}")
    home_view = HomeView(None)
    home_view.show()
    sys.exit(app.exec())       