""" File for the main window of the application, which contains the home page, the game and the settings page.
The main window is responsible for switching between the different pages and managing the overall layout of the application using 
a QStackedWidget."""

from PyQt6.QtWidgets import QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from ui.home_page import HomeView
from ui.game_page import GameView
from ui.settings_page import SettingsView
from Control import Control

class MainUI(QMainWindow):

    def __init__(self, chess_model, control, communication, cam):

        super().__init__()
        self.chess_model = chess_model
        self.control = control
        self.cam = cam

        self.setWindowTitle("CNChess")

        # Load and apply global QSS stylesheet
        qss_path = os.path.join(os.path.dirname(__file__), "cnchess_theme.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        else:
            print(f"Warning: QSS theme file not found at {qss_path}")

        # Create the stacked widget to hold the different pages
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Create the different pages
        self.home_page = HomeView(chess_model)
        self.game_page = GameView(chess_model,self.control, communication, self.cam)
        self.settings_page = SettingsView(communication, cam)

        # Add the pages to the stacked widget
        self.stacked_widget.addWidget(self.home_page)
        self.stacked_widget.addWidget(self.game_page)
        self.stacked_widget.addWidget(self.settings_page)

        # Connect controller signals to page-switching methods
        self.home_page.home_page_controller.start_game_signal.connect(self.switch_to_game_page)
        self.game_page.game_page_controller.show_settings_signal.connect(self.switch_to_settings_page)
        self.game_page.game_page_controller.return_home_signal.connect(self.switch_to_home_page)
        self.settings_page.controller.game_page_signal.connect(self.switch_to_game_page)
        self.game_page.game_page_controller.send_gantry_position.connect(self.settings_page.update_coord)


    def switch_to_home_page(self):
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.game_page.game_page_controller.reset_board()

    def switch_to_game_page(self, game_started=False):
        self.stacked_widget.setCurrentWidget(self.game_page)
        if not game_started:
            self.game_page.setup_board()
      
    def switch_to_settings_page(self):
        self.stacked_widget.setCurrentWidget(self.settings_page)
    
    def closeEvent(self, event):
        """Clean up all threads when the application window is closed."""
        print("[INFO] Closing application and terminating all threads...")
        self.cleanup_all_threads()
        event.accept()
    
    def cleanup_all_threads(self):
        """Terminate all worker threads in all pages before closing."""
        # Clean up game page threads
        if hasattr(self.game_page, 'cleanup_threads'):
            self.game_page.cleanup_threads()
        
        # Clean up settings page threads
        if hasattr(self.settings_page, 'cleanup_threads'):
            self.settings_page.cleanup_threads()
    
    def __del__(self):
        """Destructor to ensure cleanup on object destruction."""
        try:
            self.cleanup_all_threads()
        except:
            pass  # Ignore errors during destruction