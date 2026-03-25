"""File containing the game page of the application, which is where the user plays the chess game. 
It contains the chess board, move history, and buttons to undo moves, resign, and start a new game. 
You can access th """

import os
import sys
import chess
import re

import math

from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QApplication, QSizePolicy, QListWidget, QListWidgetItem, QDialog
from PyQt6.QtCore import QObject, pyqtSignal, QSize, QThread, Qt, QPointF, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QColor, QPainter, QPen, QPolygonF
from PyQt6 import uic

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from Communication import Communication
from Control import Control
from ui.dialog_ui import WinnerDialog, DrawDialog, WaitingDialog, TurnIndicatorWidget


LIGHT_SQUARE_COLOR = "#F0D9B5"
DARK_SQUARE_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#B9B9B9"  # Yellow highlight for selected piece and possible moves
WHITE_SQUARE_COLORS = (LIGHT_SQUARE_COLOR, DARK_SQUARE_COLOR)
BLACK_SQUARE_COLORS = (DARK_SQUARE_COLOR, LIGHT_SQUARE_COLOR)
SQUARE_SIZE_MM = 50.8


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


class WaitForButtonWorker(QObject):
    """Worker thread to wait for ESP button press without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, communication):
        super().__init__()
        self.communication = communication

    def run(self):
        """Execute wait_for_button_press in the worker thread."""
        try:
            result = self.communication.wait_for_button_press()
            if result:
                self.finished.emit()
            else:
                self.error.emit("No button press detected")
        except Exception as e:
            self.error.emit(f"Error while waiting for button press: {str(e)}")

class ChessClock(QWidget):

    outOfTime_signal = pyqtSignal(int)

    def __init__(self, initial_time, clock_label, color="white"):
        """Initial time in seconds"""
        super().__init__()
        self.timer = QTimer()
        self.time_left = initial_time
        self.initial_time = initial_time
        self.timer.timeout.connect(self.tick)
        self.clock_label = clock_label
        self.update_display()
        self.color = color

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
            self.outOfTime_signal.emit(self.color)

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
        
        self.stop()
        self.time_left = self.initial_time
        self.update_display()

    def stop(self):

        if self.timer.isActive():
            self.timer.stop()    

class GameView(QWidget):

    def __init__(self, chess_game, control, communication, cam):

        super().__init__()

        self.chess_game = chess_game
        self.control = control
        self.cam = cam
       
        # Load the UI from the .ui file
        ui_path = os.path.join(os.path.dirname(__file__), 'gamePage.ui')

        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found at path: {ui_path}")

        uic.loadUi(ui_path, self)

        settings_button = self.findChild(QPushButton, "settingsButton")
        quit_button = self.findChild(QPushButton, "quitButton")  
        right_layout = self.findChild(QVBoxLayout, "rightLayout")
        resign_button = self.findChild(QPushButton, "resignButton")
        start_button = self.findChild(QPushButton, "startButton")
        move_back_button = self.findChild(QPushButton, "moveBackButton")
        move_forward_button = self.findChild(QPushButton, "moveForwardButton")
        self.move_list = self.findChild(QListWidget, "moveList")
        self.white_timer_display = self.findChild(QLabel, 'whiteTimer')
        self.black_timer_display = self.findChild(QLabel, 'blackTimer')
        self.black_score = self.findChild(QLabel, 'blackScore')
        self.white_score = self.findChild(QLabel, 'whiteScore')
        
        # Replace the simple turn_indicator label with the new TurnIndicatorWidget
        old_turn_indicator = self.findChild(QLabel, 'labelTurn')
        if old_turn_indicator:
            # Find the parent layout (layout_Timers)
            layout_timers = self.findChild(QHBoxLayout, 'layout_Timers')
            if layout_timers:
                # Get the index of the old turn indicator
                index = layout_timers.indexOf(old_turn_indicator)
                # Remove the old widget
                layout_timers.removeWidget(old_turn_indicator)
                old_turn_indicator.deleteLater()
                # Create and insert the new TurnIndicatorWidget
                self.turn_indicator = TurnIndicatorWidget()
                layout_timers.insertWidget(index, self.turn_indicator)
            else:
                # Fallback if layout not found
                self.turn_indicator = TurnIndicatorWidget()
        else:
            # Fallback if old indicator not found
            self.turn_indicator = TurnIndicatorWidget()

        right_layout.removeItem(right_layout.itemAt(1))  
        resize_board = AspectRatioWidget(ChessBoardWidget())
        right_layout.insertWidget(1,resize_board)
        self.board = resize_board.board_widget
        
        self.white_clock = ChessClock(initial_time=600, clock_label=self.white_timer_display, color="white")
        self.black_clock = ChessClock(initial_time=600, clock_label=self.black_timer_display, color="black")
        self.game_page_controller = GamePageController(chess_game,self, self.control, communication, self.cam)

        settings_button.clicked.connect(self.game_page_controller.settings_button_clicked)     
        quit_button.clicked.connect(self.game_page_controller.quit_game)
        resign_button.clicked.connect(self.game_page_controller.reset_board)
        start_button.clicked.connect(self.start_time)
        move_back_button.clicked.connect(self.game_page_controller.move_back_position)
        move_forward_button.clicked.connect(self.game_page_controller.move_forward_position)
    
    def cleanup_threads(self):
        """Clean up all worker threads in the game page."""
        self.game_page_controller.wait_for_threads()

    def setup_board(self):
        color = self.chess_game.get_player_color()
        self.board.set_player_color(color)
        self.chess_game.reset_game()
        self.board.paint_board() # Clear any existing highlights before updating the boar
        self.board.update_board(self.chess_game.get_board_state())

    def start_time(self):

        color = self.chess_game.get_player_color()

        self.white_clock.reset_clock()
        self.black_clock.reset_clock()

        #If player is black launch first move of computer as white
        if not color :
            self.turn_indicator.update_turn("black")
            self.game_page_controller.start_game_black_signal.emit()

        else :        
            self.turn_indicator.update_turn("white")
            # Human starts as white: wait asynchronously for the board button press.
            self.game_page_controller.wait_for_button_press_async()

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
    send_gantry_position = pyqtSignal(float, float, bool)

    def __init__(self, chess_game, view=None, control=None, communication=None, cam=None):
        super().__init__()
        self.chess_game = chess_game
        self.view = view
        self.cam = cam

         # Initialize worker threads
        self.send_path_worker = None
        self.send_path_thread = None
        self.wait_button_worker = None
        self.wait_button_thread = None

        self.board_widget = self.view.board
        self.board = []
        self.board_positions = []
        board_state = self.chess_game.get_board_state()
        self.board_positions.append(board_state)  # Store the initial board state
        self.board_positions_index = 0
        self.control = control
        self.control.update_board_state(board_state)
        self.communication = communication

        self.selected_piece = None  # Track the currently selected piece for move selection
        self.board_widget.squared_clicked_signal.connect(self.handle_square_click)
        self.start_game_black_signal.connect(self.computer_move)
        self.view.white_clock.outOfTime_signal.connect(self.outOfTime)
        self.view.black_clock.outOfTime_signal.connect(self.outOfTime)
  
    def settings_button_clicked(self):
        self.show_settings_signal.emit()

    def quit_game(self):
        self.wait_for_threads()
        self.return_home_signal.emit()

    def wait_for_thread(self):
        """Wait for any running send_path thread to fully finish."""
        if self.send_path_thread is not None:
            if self.send_path_thread.isRunning():
                self.send_path_thread.quit()
                self.send_path_thread.wait()
            self.send_path_thread = None
            self.send_path_worker = None

    def wait_for_button_thread(self):
        """Wait for any running button-wait thread to fully finish."""
        if self.wait_button_thread is not None:
            if self.wait_button_thread.isRunning():
                self.wait_button_thread.quit()
                self.wait_button_thread.wait()
            self.wait_button_thread = None
            self.wait_button_worker = None

    def wait_for_threads(self):
        """Wait for all communication worker threads to finish."""
        self.wait_for_thread()
        self.wait_for_button_thread()

    def send_path_async(self, path):
        """Send path to device asynchronously without blocking the UI."""
        # Wait for any previous thread to finish before starting a new one
        self.wait_for_thread()

        # Create worker and thread (parent=self keeps thread alive)
        self.send_path_worker = SendPathWorker(self.communication, path)
        self.send_path_thread = QThread(parent=self)
        self.send_path_worker.moveToThread(self.send_path_thread)
        
        # Connect signals
        self.send_path_thread.started.connect(self.send_path_worker.run)
        self.send_path_worker.finished.connect(self.on_send_path_finished)
        self.send_path_worker.finished.connect(self.send_path_thread.quit)
        self.send_path_worker.error.connect(self.on_send_path_error)
        self.send_path_worker.error.connect(self.send_path_thread.quit)
        
# Show waiting state and start thread
        self.view.turn_indicator.show_waiting("Sending move to device...\nPlease wait.")
        self.send_path_thread.start()

    def wait_for_button_press_async(self):
        """Wait for physical button press asynchronously without blocking the UI."""
        self._start_button_wait("Waiting for button press...\nPlease play your move.")

    def _start_button_wait(self, message: str):
        """Internal method to start waiting for button press with a custom message."""
        self.wait_for_button_thread()

        self.wait_button_worker = WaitForButtonWorker(self.communication)
        self.wait_button_thread = QThread(parent=self)
        self.wait_button_worker.moveToThread(self.wait_button_thread)

        self.wait_button_thread.started.connect(self.wait_button_worker.run)
        self.wait_button_worker.finished.connect(self.on_wait_button_finished)
        self.wait_button_worker.finished.connect(self.wait_button_thread.quit)
        self.wait_button_worker.error.connect(self.on_wait_button_error)
        self.wait_button_worker.error.connect(self.wait_button_thread.quit)

        self.view.turn_indicator.show_waiting(message)
        self.wait_button_thread.start()

    def on_send_path_finished(self):
        """Handler when send_path completes successfully."""
        print("Path sent successfully to device")
        self.view.white_clock.toggle_timer()
        self.view.black_clock.toggle_timer()
        self.wait_for_button_press_async()

    def on_send_path_error(self, error_msg):
        """Handler when send_path encounters an error."""
        self.view.turn_indicator.hide_waiting()
        self.view.white_clock.toggle_timer()
        self.view.black_clock.toggle_timer()
        print(f"Error: {error_msg}")

    def on_wait_button_finished(self):
        """Handler when the ESP button press is detected."""
        print("Button press detected")

        self.view.turn_indicator.hide_waiting()
        self.board_widget.clear_trajectory()

        cam_result = self.cam.process_image()
        try:
            move = chess.Move.from_uci(cam_result['move']['uci'])
        except Exception as e:
            print(f"Caught error while parsing move from camera result: {str(e)}. Camera result was: {cam_result}")
            return
        if self.chess_game.validate_move(move):
            moved_piece = self.chess_game.get_board().piece_at(move.from_square)
            piece = moved_piece.symbol().upper() if moved_piece is not None else "?"
            self.update_list(move=f"{piece}{move.to_square}", turn=self.chess_game.get_turn())
            path = self.make_move(move)
            self.view.white_clock.toggle_timer()
            self.view.black_clock.toggle_timer()
            self.update_chess_board()  # Update the board display after making the move
            self.selected_piece = None  # Reset the selected piece after making a move

            game_outcome = self.handle_game_outcome()
            if not game_outcome :
                self.computer_move()
        else:
            print(f"Camera processing result: Invalid move detected: {move.uci()}. Waiting for valid move.")
            # Show error message and wait for next button press
            # self._start_button_wait("Invalid move detected!\nPlease press the button again to try a valid move.")

    def on_wait_button_error(self, error_msg):
        """Handler when waiting for button press fails or times out."""
        self.view.turn_indicator.hide_waiting()
        self.cam.process_image()
        self.view.white_clock.toggle_timer()
        self.view.black_clock.toggle_timer()
        print(f"Error: {error_msg}. Continuing without button confirmation.")

    def handle_square_click(self, row, col):
        """Handle click events on the squares. This is where you would implement move selection and execution logic."""
        self.board_widget.clear_trajectory()

        if self.selected_piece is None:
            self.check_piece_selected(row,col)
        
        else :
            from_square = self.coordinate_to_square(*self.selected_piece)
            to_square = self.coordinate_to_square(row, col)
        
            try:    
                move = chess.Move.from_uci(from_square + to_square)

                if self.chess_game.is_promotion_move(move):
                    print("Promotion move detected, showing promotion dialog")
                    promotion_dialog = PromotionWidget(self.chess_game.get_player_color())
                    result = promotion_dialog.exec()

                    if result:
                        move.promotion = promotion_dialog.chosen_piece
                    else :
                        self.check_piece_selected(row, col)  # Update highlights for the new position after the move
                        return # If no piece chosen, cancel the move and wait for a valid move
    
                if self.chess_game.validate_move(move):

                    piece = self.board_widget.board[self.selected_piece[0]][self.selected_piece[1]].upper()
                    self.update_list(move=f"{piece}{to_square}", turn=self.chess_game.get_turn())
                    print(f"Camera processing result: Actual move: {move.uci()}")
                    path = self.make_move(move)
                    self.view.white_clock.toggle_timer()
                    self.view.black_clock.toggle_timer()
                    self.update_chess_board()  # Update the board display after making the move
                    self.selected_piece = None  # Reset the selected piece after making a move

                    game_outcome = self.handle_game_outcome()
                    if not game_outcome :
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
            self.selected_piece = None
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
            self.send_gantry_position.emit(path[-1].position.x * SQUARE_SIZE_MM, path[-1].position.y * SQUARE_SIZE_MM, True)  # Emit the final position of the path for gantry movement
            
            self.update_chess_board()  # Update the board display after computer move
            self.board_widget.set_trajectory(path)

            # Send path asynchronously to avoid blocking the UI
            self.send_path_async(path)
            self.handle_game_outcome()        
       
    def handle_game_outcome(self):

        game_outcome = self.chess_game.check_game_outcome()

        if game_outcome :
            self.stop_clocks()
            if not game_outcome == "draw":
                # Get both king positions
                white_king_pos = self.chess_game.get_board().king(chess.WHITE)
                black_king_pos = self.chess_game.get_board().king(chess.BLACK)

                checkmate_dialog = WinnerDialog(winner_color=game_outcome)
                chess_game_outcome = chess.WHITE if game_outcome == "white" else chess.BLACK
                if chess_game_outcome != self.chess_game.get_player_color(): 
                    if self.chess_game.get_player_color() == chess.WHITE:
                        path = self.make_move(chess.Move.from_uci(f"{chess.square_name(black_king_pos)}{chess.square_name(white_king_pos)}"))
                    else :
                        path = self.make_move(chess.Move.from_uci(f"{chess.square_name(white_king_pos)}{chess.square_name(black_king_pos)}"))
                    self.wait_for_threads()
                    self.send_path_async(path)
                
                # Hide the waiting indicator before showing the checkmate dialog
                self.view.turn_indicator.hide_waiting()
                result = checkmate_dialog.exec()

            else : 
                draw_dialog = DrawDialog()
                result = draw_dialog.exec()

            #If want to play again switch to home page
            if result : 
                self.return_home_signal.emit()
            else : 
                self.wait_for_threads()
                sys.exit()    

        return game_outcome       
    
    def outOfTime(self, losing_color):

        color = "white" if losing_color == "white" else "black"

        self.stop_clocks()
        timeout_dialog = WinnerDialog(winner_color=color, reason="timeout")
        result = timeout_dialog.exec()

        if result : 
            self.return_home_signal.emit()
        else : 
            self.wait_for_threads()
            sys.exit()

    def update_chess_board(self):

        self.board_widget.paint_board() # Clear any existing highlights before updating the boar
        board_state = self.chess_game.get_board_state()
        self.board_positions.append(board_state)  # Store the new board state after the move
        self.board_positions_index = len(self.board_positions) - 1  # Update index to the latest position after making a move
        self.board_widget.update_board(board_state)

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

    def move_back_position(self):
        print("Moving back position")
        print(self.board_positions_index)
        if self.board_positions_index > 0 :
            self.board_positions_index-=1
            previous_fen = self.board_positions[self.board_positions_index]
            self.board_widget.update_board(previous_fen)
            self.board_widget.paint_board()     

    def move_forward_position(self):
        if self.board_positions_index < len(self.board_positions) - 1 :
            self.board_positions_index+=1
            previous_fen = self.board_positions[self.board_positions_index]
            self.board_widget.update_board(previous_fen)
            self.board_widget.paint_board()            

    def update_score(self):

        white_score = self.chess_game.get_material_evaluation(chess.WHITE)
        black_score = self.chess_game.get_material_evaluation(chess.BLACK)
        
        score = white_score - black_score

        if score > 0 :
            self.view.white_score.setText(f"+{score}")
            self.view.black_score.setText("")
            
        elif score < 0 :
            self.view.black_score.setText(f"+{-score}")  
            self.view.white_score.setText("")
        else :
            self.reset_score()

    def reset_score(self):
        self.view.white_score.setText("")
        self.view.black_score.setText("")        

    def clear_list(self):
        self.view.move_list.clear() 
    
    def make_move(self, move):
        self.control.update_board_state(self.chess_game.get_board_state())
        path = self.control.get_path(move, self.chess_game.get_board())

        self.control.print_path(path)
        self.chess_game.make_move(move)
        self.update_score()

        turn = "white" if self.chess_game.get_turn() else "black"
        self.view.turn_indicator.update_turn(turn)

        return path

    def reset_board(self):
        self.chess_game.reset_game()
        self.reset_score()
        self.clear_list()
        self.board_widget.clear_trajectory()
        self.board_widget.update_board(self.chess_game.get_board_state())
        self.board_widget.paint_board()
        self.selected_square = None  # Reset selected square when resetting the board
        self.view.white_clock.reset_clock()
        self.view.black_clock.reset_clock()

    def stop_clocks(self) :
        self.view.white_clock.stop()
        self.view.black_clock.stop()


class TrajectoryOverlay(QWidget):
    """Transparent overlay that draws the move trajectory on top of the board."""

    TRAJECTORY_COLOR = QColor(220, 50, 50, 200)
    EAT_COLOR = QColor(50, 220, 50, 200)
    POINT_COLOR = QColor(50, 50, 220, 200)
    LINE_WIDTH = 3
    DOT_RADIUS = 4
    ARROW_SIZE = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.trajectory = []  # list of (x, y) in 1-based board coords
        self.player_color = chess.WHITE

    def set_trajectory(self, path, player_color):
        """Set trajectory from a list of Command objects."""
        self.trajectory = [(cmd.position.x, cmd.position.y) for cmd in path]
        self.magnet_states = [cmd.magnet_state for cmd in path]
        self.player_color = player_color
        self.update()

    def clear_trajectory(self):
        self.trajectory = []
        self.update()

    def _to_pixel(self, x, y):
        """Convert 1-based board coordinates to pixel position on the widget."""
        sw = self.width() / 8.0
        sh = self.height() / 8.0
        if self.player_color == chess.WHITE:
            px = sw * (x - 0.5)
            py = sh * (8.5 - y)
        else:
            px = sw * (8.5 - x)
            py = sh * (y - 0.5)
        return QPointF(px, py)

    def paintEvent(self, event):
        if len(self.trajectory) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(self.TRAJECTORY_COLOR, self.LINE_WIDTH)
        painter.setPen(pen)

        points = [self._to_pixel(x, y) for x, y in self.trajectory]

        # Draw path lines
        for i in range(len(points) - 1):
            if self.magnet_states[i] == False:
                painter.setPen(QPen(self.EAT_COLOR, self.LINE_WIDTH, Qt.PenStyle.DashLine))
                continue
            painter.drawLine(points[i], points[i + 1])

        # Draw dots at waypoints
        painter.setBrush(self.POINT_COLOR)
        painter.setPen(Qt.PenStyle.NoPen)
        for pt in points:
            painter.drawEllipse(pt, self.DOT_RADIUS, self.DOT_RADIUS)

        # Draw arrowhead at the final point
        if len(points) >= 2:
            p1 = points[-2]
            p2 = points[-1]
            angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            arrow_p1 = QPointF(
                p2.x() - self.ARROW_SIZE * math.cos(angle - math.pi / 6),
                p2.y() - self.ARROW_SIZE * math.sin(angle - math.pi / 6),
            )
            arrow_p2 = QPointF(
                p2.x() - self.ARROW_SIZE * math.cos(angle + math.pi / 6),
                p2.y() - self.ARROW_SIZE * math.sin(angle + math.pi / 6),
            )
            painter.setBrush(self.TRAJECTORY_COLOR)
            painter.drawPolygon(QPolygonF([p2, arrow_p1, arrow_p2]))

        painter.end()


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
        self.trajectory_overlay = TrajectoryOverlay(self)
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
   
        highlight_color = QColor(base_color).darker(175).name()  # Create a lighter version of the base color for highlighting

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.trajectory_overlay.setGeometry(0, 0, event.size().width(), event.size().height())
        self.trajectory_overlay.raise_()

    def set_trajectory(self, path):
        """Show the move trajectory on the board."""
        self.trajectory_overlay.set_trajectory(path, self.player_color)

    def clear_trajectory(self):
        """Remove the trajectory overlay."""
        self.trajectory_overlay.clear_trajectory()

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
    

class PromotionWidget(QDialog): 

    promotion_signal = pyqtSignal(int)  # Signal to emit the chosen promotion piece as chess piece type (e.g., chess.QUEEN)

    def __init__(self, player_color):
        super().__init__()
        self.setFixedSize(200, 100)
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.piece_chosen_dict = {
            'Q': chess.QUEEN,
            'R': chess.ROOK,
            'B': chess.BISHOP,
            'N': chess.KNIGHT,}

        pieces = ['Q', 'R', 'B', 'N'] if player_color == chess.WHITE else ['q', 'r', 'b', 'n']
        for piece in pieces:
            button = QPushButton(piece)
            button.clicked.connect(lambda checked, p=piece: self.promote(p))
            layout.addWidget(button)

    def promote(self, piece):
        self.chosen_piece = self.piece_chosen_dict[piece.upper()]
        self.accept()  # Close the promotion dialog after selection    
            
if __name__ == "__main__":

    # Ensure the parent package (python/) is on sys.path so CNChess can be imported
    from CNChess import CNChess   

    chess_model = CNChess()
    app = QApplication(sys.argv)
    game_view = GameView(chess_model, Control())
    game_view.show()
    sys.exit(app.exec())


