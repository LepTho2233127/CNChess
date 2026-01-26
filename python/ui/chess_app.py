"""PyQt Chess Application - Main entry point for the chess UI application."""

import sys
import os
from PyQt6.QtWidgets import QApplication

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from CNChess import CNChess
from chess_view import ChessView
from chess_controller import ChessController


def main():
    """Main application entry point."""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create the CNChess instance
    cn_chess = CNChess()
    
    # Create view and controller
    view = ChessView(cn_chess)
    controller = ChessController(cn_chess, view)
    
    # Set the controller in the view
    view.controller = controller
    
    # Show the window
    view.show()
    
    # Run the application event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
