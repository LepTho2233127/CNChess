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
        """Initialize the main application window with pages and signal connections.
        
        Args:
            chess_model: Model instance for chess game state management.
            control: Control instance for game control operations.
            communication: Communication instance for hardware communication.
            cam: Camera instance for board capture and analysis.
        
        Return:
            None
        """
        super().__init__()
        self.chess_model = chess_model
        self.control = control
        self.communication = communication
        self.cam = cam
        self.last_page = "home"
        self._cleaned_up = False

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
        self.home_page.home_page_controller.settings_signal.connect(self.switch_to_settings_page)
        self.game_page.game_page_controller.show_settings_signal.connect(self.switch_to_settings_page)
        self.game_page.game_page_controller.return_home_signal.connect(self.switch_to_home_page)
        self.settings_page.controller.back_button_signal.connect(self.back_button_settings_page)
        self.game_page.game_page_controller.send_gantry_position.connect(self.settings_page.update_coord)

    def switch_to_home_page(self):
        """Switch the main window display to the home page and reset the game board.
        
        Args:
            None
        
        Return:
            None
        """
        self.last_page = "home"
        self.stacked_widget.setCurrentWidget(self.home_page)
        self.game_page.game_page_controller.reset_board()

    def switch_to_game_page(self):
        """Switch the main window display to the game page and initialize the board.
        
        Args:
            None
        
        Return:
            None
        """
        self.last_page = "game"
        self.stacked_widget.setCurrentWidget(self.game_page)
        self.game_page.setup_board()
      
    def switch_to_settings_page(self):
        """Switch the main window display to the settings page.
        
        Args:
            None
        
        Return:
            None
        """
        self.stacked_widget.setCurrentWidget(self.settings_page)
        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')
        self.settings_page.update_captured_image(img_path)

    def back_button_settings_page(self):
        """Return to the previous page (game or home) from the settings page.
        
        Args:
            None
        
        Return:
            None
        """
        if self.last_page == "game":
            self.stacked_widget.setCurrentWidget(self.game_page)
        else:
            self.stacked_widget.setCurrentWidget(self.home_page)    
    
    def closeEvent(self, event):
        """Handle application window close event and perform cleanup.
        
        Args:
            event: QCloseEvent instance triggered by window closure.
        
        Return:
            None
        """
        print("[INFO] Closing application and terminating all threads...")
        self.cleanup_all_threads()
        event.accept()
    
    def cleanup_all_threads(self):
        """Terminate all worker threads and release resources before closing.
        
        Args:
            None
        
        Return:
            None
        """
        if self._cleaned_up:
            return
        self._cleaned_up = True

        # First signal communication shutdown so blocked workers can exit quickly.
        if self.communication is not None:
            try:
                self.communication.shutdown()
            except Exception as e:
                print(f"[WARN] Communication shutdown failed: {e}")

        # Clean up game page threads
        try:
            self.game_page.cleanup_threads()
        except Exception as e:
            print(f"[WARN] Game page cleanup failed: {e}")
        
        # Clean up settings page threads
        try:
            self.settings_page.cleanup_threads()
        except Exception as e:
            print(f"[WARN] Settings page cleanup failed: {e}")

        # Release camera handle at shutdown.
        if self.cam is not None:
            try:
                self.cam.release()
            except Exception as e:
                print(f"[WARN] Camera release failed: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup on object destruction.
        
        Args:
            None
        
        Return:
            None
        """
        try:
            self.cleanup_all_threads()
        except Exception:
            pass  # Ignore errors during destruction