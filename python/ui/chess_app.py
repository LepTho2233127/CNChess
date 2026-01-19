"""PyQt Chess Application - Main entry point for the chess UI application."""

import sys
from PyQt6.QtWidgets import QApplication
from chess_model import ChessModel
from chess_view import ChessView
from chess_controller import ChessController


def main():
    """Main application entry point."""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create MVC components
    model = ChessModel()
    view = ChessView(model)
    controller = ChessController(model, view)
    
    # Set the controller in the view for signal handling
    view.controller = controller
    
    # Show the window
    view.show()
    
    # Run the application event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
