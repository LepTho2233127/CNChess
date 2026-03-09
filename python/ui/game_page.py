"""File containing the game page of the application, which is where the user plays the chess game. 
It contains the chess board, move history, and buttons to undo moves, resign, and start a new game. 
You can access th """

import os
import sys
import chess
import re

from chess import Termination

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QApplication, QSizePolicy, QListWidget, QListWidgetItem, QDialog, QGraphicsBlurEffect
from PyQt6.QtCore import QObject, pyqtSignal, QSize, QThread, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6 import uic

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Communication import Communication
from Control import Control
from ui.dialog_ui import CheckmateDialog


LIGHT_SQUARE_COLOR = "#F0D9B5"
DARK_SQUARE_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#B9B9B9"  # Yellow highlight for selected piece and possible moves
WHITE_SQUARE_COLORS = (LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)
BLACK_SQUARE_COLORS = (DARK_SQUARE_COLOR, LIGHT_SQUARE_COLOR)


class SendPathWorker(QObject):
    """Worker thread to send path commands without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, communication, path):
        super().__init__()
        self.communication = communication
        self.path = path
    
    def run(self):
        """Execute send_path in the worker thread."""
        try:
            result = self.communication.send_path(self.path)
            if not result:
                self.error.emit("Failed to send path to device")
            else:
                self.finished.emit()
        except Exception as e:
            self.error.emit(f"Error sending path: {str(e)}")


class WaitingDialog(QDialog):
    """Simple waiting dialog to show while path is being sent."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Move")
        self.setModal(True)
        self.setFixedSize(300, 100)
        
        layout = QVBoxLayout()
        label = QLabel("Sending move to device...\nPlease wait.")
        layout.addWidget(label)
        self.setLayout(layout)
        
        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.left() + (parent_geometry.width() - 300) // 2,
                parent_geometry.top() + (parent_geometry.height() - 100) // 2
            )

class ChessClock():

    def __init__(self, initial_time, clock_label):
        """Initial time in seconds"""

        self.timer = QTimer()
        self.time_left = initial_time
        self.initial_time = initial_time
        self.timer.timeout.connect(self.tick)
        self.clock_label = clock_label
        self.update_display()

        self.clock_label.setStyleSheet("""
        background-color: #3b2f2f;
        color: #f3e5ab;
        border: 4px solid #8b5a2b;
        border-radius: 5px;
        padding: 20px;
        font-family: 'Georgia', serif;
        font-size: 32px;
        font-weight: bold;
    """)

    def tick(self):
        
        if self.time_left > 0:
            self.time_left -= 1
            self.update_display()
        else :
            self.timer.stop()
            self.clock_label.setText("00:00")
            print("No time left")    

    def update_display(self):

        minutes, seconds = divmod(self.time_left, 60)
        self.clock_label.setText(f"{minutes:02d}:{seconds:02d}")

    def toggle_timer(self):

        if self.timer.isActive():
            self.timer.stop()
        else :
            self.timer.start(1000) #Every second
         
    def reset_clock(self):
        
        if self.timer.isActive():
            self.timer.stop()
        self.time_left = self.initial_time
        self.update_display()

class GameView(QWidget):

    def __init__(self, chess_game, control):

        super().__init__()

        self.chess_game = chess_game
        self.control = control
       
        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'gamePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        settings_button = self.findChild(QPushButton, "settingsButton")
        quit_button = self.findChild(QPushButton, "quitButton")  
        right_layout = self.findChild(QVBoxLayout, "rightLayout")
        resign_button = self.findChild(QPushButton, "resignButton")
        self.move_list = self.findChild(QListWidget, "moveList")
        self.white_timer_display = self.findChild(QLabel, 'whiteTimer')
        self.black_timer_display = self.findChild(QLabel, 'blackTimer')
        self.turn_indicator = self.findChild(QLabel, 'labelTurn')

        right_layout.removeItem(right_layout.itemAt(1))  
        resize_board = AspectRatioWidget(ChessBoardWidget())
        right_layout.insertWidget(1,resize_board)
        self.board = resize_board.board_widget

        self.white_clock = ChessClock(initial_time=600, clock_label=self.white_timer_display)
        self.black_clock = ChessClock(initial_time=600, clock_label=self.black_timer_display)

        self.game_page_controller = GamePageController(chess_game,self, self.control)

        settings_button.clicked.connect(self.game_page_controller.settings_button_clicked)     
        quit_button.clicked.connect(self.game_page_controller.quit_game)
        resign_button.clicked.connect(self.game_page_controller.reset_board)
 
    def start_chess_board(self):

        color = self.chess_game.get_player_color()
        self.board.set_player_color(color)
        self.board.paint_board() # Clear any existing highlights before updating the boar
        self.board.update_board(self.chess_game.get_board_state())

        #If player is black launch first move of computer as white
        if not color :
            self.turn_indicator.setStyleSheet("background-color:black")
            self.game_page_controller.start_game_black_signal.emit()

        else :          
            self.turn_indicator.setStyleSheet("background-color:white")

        self.white_clock.toggle_timer()
        
    def update_highlighted_squares(self, squares):
        """Highlight the given squares on the board."""

        self.board.paint_board()  # Clear existing highlights before applying new ones

        for row, col in squares:
            self.board.update_square_highlight(row, col)    
        
class GamePageController(QObject):
    # Define signals for navigation
    show_settings_signal = pyqtSignal()
    start_game_black_signal = pyqtSignal() #Signal for start of game as black
    return_home_signal = pyqtSignal()

    def __init__(self, chess_game, view=None, control=None):
        super().__init__()
        self.chess_game = chess_game
        self.view = view 

         # Initialize worker thread and waiting dialog
        self.send_path_worker = None
        self.send_path_thread = None
        self.waiting_dialog = WaitingDialog(self.view)     

        self.board_widget = self.view.board
        self.board = []
        self.control = control
        self.control.update_board_state(self.chess_game.get_board_state())
        self.communication = Communication()

        self.selected_piece = None  # Track the currently selected piece for move selection
        self.board_widget.squared_clicked_signal.connect(self.handle_square_click)
        self.start_game_black_signal.connect(self.computer_move)
        
    def settings_button_clicked(self):
        self.show_settings_signal.emit()

    def quit_game(self):
        self.return_home_signal.emit()

    def send_path_async(self, path):
        """Send path to device asynchronously without blocking the UI."""
        # Create worker and thread
        self.send_path_worker = SendPathWorker(self.communication, path)
        self.send_path_thread = QThread()
        self.send_path_worker.moveToThread(self.send_path_thread)
        
        # Connect signals
        self.send_path_thread.started.connect(self.send_path_worker.run)
        self.send_path_worker.finished.connect(self.on_send_path_finished)
        self.send_path_worker.finished.connect(self.send_path_thread.quit)
        self.send_path_worker.error.connect(self.on_send_path_error)
        self.send_path_worker.error.connect(self.send_path_thread.quit)
        self.send_path_thread.finished.connect(self.send_path_worker.deleteLater)
        self.send_path_thread.finished.connect(self.send_path_thread.deleteLater)
        
        # Show waiting dialog and start thread
        self.waiting_dialog.show()
        self.send_path_thread.start()

    def on_send_path_finished(self):
        """Handler when send_path completes successfully."""
        self.waiting_dialog.hide()
        print("Path sent successfully to device")

    def on_send_path_error(self, error_msg):
        """Handler when send_path encounters an error."""
        self.waiting_dialog.hide()
        print(f"Error: {error_msg}")


    def handle_square_click(self, row, col):
        """Handle click events on the squares. This is where you would implement move selection and execution logic."""
        
        if self.selected_piece is None:

            self.check_piece_selected(row,col)
           
        else :
            from_square = self.coordinate_to_square(*self.selected_piece)
            to_square = self.coordinate_to_square(row, col)
         
            try:    
                move = chess.Move.from_uci(from_square + to_square)
    
                if self.chess_game.validate_move(move):

                    piece = self.board_widget.board[self.selected_piece[0]][self.selected_piece[1]].upper()
                    self.update_list(move=f"{piece}{to_square}", turn=self.chess_game.get_turn())
                    
                    path = self.make_move(move)
                    self.update_chess_board()  # Update the board display after making the move
                    self.selected_piece = None  # Reset the selected piece after making a move

                    self.handle_game_outcome()
                    self.computer_move()
                else:
                    # If the move is not valid, reset the selection and highlights
                    self.check_piece_selected(row, col)  # Update highlights for the new position after the move
            except ValueError:
                pass # Invalid move format, happens when you click on the same square as the selected piece, just ignore it and wait for a valid move       

    def check_piece_selected(self, row, col): 

        player_color = self.chess_game.get_player_color()
        piece = self.board_widget.board[row][col]
        if piece != '_' and (( player_color == chess.WHITE and piece.isupper()) or 
                                                (player_color == chess.BLACK and piece.islower())):
            
            self.selected_piece = (row, col)
            legal_moves = self.chess_game.get_legal_moves_from_square(self.coordinate_to_square(row, col))

            if player_color : 
                highlighted_squares = [(7 - chess.square_rank(move.to_square), chess.square_file(move.to_square)) for move in legal_moves]
            else : 
                highlighted_squares = [(chess.square_rank(move.to_square), 7 - chess.square_file(move.to_square)) for move in legal_moves] 
            
            highlighted_squares.append((row, col))  # Also highlight the selected piece's square
            self.view.update_highlighted_squares(highlighted_squares)  # Highlight the selected piece and its legal moves

        else :
            self.view.update_highlighted_squares([(row, col)])  # Clear highlights if no piece or opponent's piece is selected                

      
    def computer_move(self):
        best_move = self.chess_game.get_next_best_move()
        if best_move and best_move != chess.Move.null():

            uci_move = best_move.uci()
            match = re.search(r'\d+', uci_move)
            split_index = match.end()
          
            to_square = uci_move[split_index:]
            piece = self.board_widget.board[(7 - chess.square_rank(best_move.from_square))][chess.square_file(best_move.from_square)].upper()
            self.update_list(move=f"{piece}{to_square}",  turn=self.chess_game.get_turn())

            path = self.make_move(best_move)
            self.update_chess_board()  # Update the board display after computer move

            # Send path asynchronously to avoid blocking the UI
            self.send_path_async(path)
            self.handle_game_outcome()
       
    def handle_game_outcome(self):

        game_outcome = self.chess_game.check_game_outcome()

        if game_outcome :
            if not game_outcome == "draw":
                checkmate_dialog = CheckmateDialog(winner_color=game_outcome)
                result = checkmate_dialog.exec()

                #If want to play again switch to home page
                if result : 
                    self.return_home_signal.emit()
                else : 
                    sys.exit()

    def update_chess_board(self):

        self.board_widget.paint_board() # Clear any existing highlights before updating the boar
        self.board_widget.update_board(self.chess_game.get_board_state())

    def coordinate_to_square(self, row, col):
        """Convert board coordinates to chess square notation (e.g., (0,0) -> 'a8')."""

        if self.chess_game.get_player_color(): 
            file = chr(ord('a') + col)
            rank = 8 - row
        else : 
            file = chr(ord('h') - col)
            rank = row + 1

        return f"{file}{rank}"
    
    def update_list(self, move, turn):

        if turn == "white":
            
            nb_move = self.view.move_list.count()+1
            self.view.move_list.addItem(QListWidgetItem(f"{nb_move}. {move}"))

        else : 
            nb_move = self.view.move_list.count()
            last_move = self.view.move_list.item(nb_move - 1)

            current_text = last_move.text()
            last_move.setText(current_text + f"\t {move}")

    def clear_list(self):
        self.view.move_list.clear() 
    
    def make_move(self, move):
        self.control.update_board_state(self.chess_game.get_board_state())
        path = self.control.get_path(move, self.chess_game.get_board())

        self.control.print_path(path)
        self.chess_game.make_move(move)
        self.view.white_clock.toggle_timer()
        self.view.black_clock.toggle_timer()

        turn = self.chess_game.get_turn()
        self.view.turn_indicator.setStyleSheet(f"background-color:{turn}")
        # self.view.board_widget.set_trajectory(path)
        # self.view.board_widget.set_computer_turn(True)

        return path

    
    def reset_board(self):
        self.chess_game.reset_game()
        self.clear_list()
        self.board_widget.update_board(self.chess_game.get_board_state())
        self.board_widget.paint_board()
        self.selected_square = None  # Reset selected square when resetting the board
        self.view.white_clock.reset_clock()
        self.view.white_clock.reset_clock()


class ChessBoardWidget(QWidget):

    squared_clicked_signal = pyqtSignal(int, int)  # Signal to emit when a square is clicked, with row and column info

    def __init__(self):
        super().__init__()
        
        self.player_color = chess.WHITE
        self.images = self.load_piece_images()
        self.board = self.fen_to_board_array(chess.STARTING_FEN)
        self.board_layout = QGridLayout()
        self.init_board()
        self.selected_square = None  # Track the currently selected square for move selection
        self.setLayout(self.board_layout)
        self.update_board(None, resize=True)  # Initial board setup with correct piece images 
            
    def init_board(self):

        for row in range(8):
            for col in range(8):
    
                square_button = GridButton()
                square_button.setMinimumSize(60, 60)  # Set a minimum size for the squares
                square_button.resize(QSize(60,60))  # Set a base size for the squares to maintain aspect ratio
                self.board_layout.addWidget(square_button, row, col)
                self.draw_piece(square_button, self.board[row][col])  # Initialize with empty squares
                square_button.clicked.connect(lambda checked, r=row, c=col: self.handle_square_click(r, c))  # Connect click event with row and column info

        for i in range(8):
            self.board_layout.setRowStretch(i, 1)  # Make rows stretchable
            self.board_layout.setColumnStretch(i, 1)  # Make columns stretchable        

        self.board_layout.setSpacing(0)
        self.board_layout.setVerticalSpacing(0)  # Remove spacing between squares

        self.paint_board()

    
    def load_piece_images(self):
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
    
    def update_board(self, board_state, resize=False):
        """Update the board display based on the new board state (FEN string)."""
        if not resize: #If this is a resize event, we don't need to update the board state from the model, just redraw the pieces with the new sizes
            self.board = self.fen_to_board_array(board_state)

        for row in range(8):
            for col in range(8):
                square_button = self.board_layout.itemAtPosition(row, col).widget()
                piece_char = self.board[row][col]
                self.draw_piece(square_button, piece_char)
        self.repaint();
    
    def draw_piece(self, button, piece_char):
        """Draw the piece on the given square button."""
        
        if piece_char in self.images:
            icon = self.images[piece_char]
            button.setIcon(icon)
            button.setIconSize(button.size())
        else:
            button.setIcon(QIcon())  # Clear the icon for empty squares     

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

        #If black flip the board 
        if not self.player_color :
            #Flip all row
            for i, row in enumerate(board) : 
                row_flip = row[::-1] 
                board[i] = row_flip

            board = board[::-1]
            
        return board  

    def update_square_highlight(self, row, col):
        """Highlight the selected square and possible move squares."""
        square_button = self.board_layout.itemAtPosition(row, col).widget()

        square_color = (row + col) % 2
        base_color = LIGHT_SQUARE_COLOR if square_color == 0 else DARK_SQUARE_COLOR
   
        highlight_color = QColor(base_color).darker(125).name()  # Create a lighter version of the base color for highlighting

        square_button.setStyleSheet(f"background-color: {highlight_color}; border: none;")  

    def handle_square_click(self, row, col):
        """Handle click events on the squares. This is where you would implement move selection and execution logic."""
       
        self.squared_clicked_signal.emit(row, col)

    def paint_board(self):
        """Paints the squares' board the right color depending of the player color"""

        for r in range(8):
            for c in range(8):
                    
                square_button = self.board_layout.itemAtPosition(r, c).widget()
                square_color = (r + c) % 2

                base_color = LIGHT_SQUARE_COLOR if square_color == 0 else DARK_SQUARE_COLOR 

                square_button.setStyleSheet(f"background-color: {base_color}; border: none;")    

        self.repaint()   

    def set_player_color(self, player_color):
        self.player_color = player_color               

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
        self.board_widget.update_board(None, resize=True)  # Update the board display on resize

 
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
    from CNChess import CNChess   

    chess_model = CNChess()
    app = QApplication(sys.argv)
    game_view = GameView(chess_model, Control())
    game_view.show()
    sys.exit(app.exec())


