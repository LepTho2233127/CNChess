import sys
import chess
import os

from PyQt6.QtWidgets import (QApplication, QDialog, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QSizePolicy, QToolButton)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QPixmap,  QTransform, QPainter, QColor

class PromotionWidget(QDialog): 

    promotion_signal = pyqtSignal(int)  # Signal to emit the chosen promotion piece as chess piece type (e.g., chess.QUEEN)

    def __init__(self, player_color):
        """Create the promotion choice dialog.
        Displays piece options (Q/R/B/N) and returns the selected promotion type.

        Args:
            player_color: Player color (chess.WHITE or chess.BLACK) used to choose correct piece icons.

        Return:
            None
        """
        super().__init__()

        self.setWindowTitle("")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("QDialog { background: transparent; }")

        # Image-only promotion choices (no padding/background/border).
        button_size = QSize(56, 56)
        icon_size = QSize(56, 56)

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.piece_chosen_dict = {
            'Q': chess.QUEEN,
            'R': chess.ROOK,
            'B': chess.BISHOP,
            'N': chess.KNIGHT,}

        piece_name_map = {
            'Q': 'queen',
            'R': 'rook',
            'B': 'bishop',
            'N': 'knight',
        }

        color_prefix = 'white' if player_color == chess.WHITE else 'black'

        pieces = ['Q', 'R', 'B', 'N'] if player_color == chess.WHITE else ['q', 'r', 'b', 'n']
        for piece in pieces:
            piece_upper = piece.upper()
            filename = f"{color_prefix}-{piece_name_map[piece_upper]}.png"
            icon_path = os.path.join(os.path.dirname(__file__), "assets", "chess_assets", "pieces_png", filename)

            button = HoverIconToolButton(self)
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            button.setAutoRaise(True)
            button.setFixedSize(button_size)
            button.setIconSize(icon_size)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setStyleSheet(
                "QToolButton { border: none; padding: 0px; margin: 0px; background: transparent; }"
                "QToolButton:hover { background: transparent; }"
                "QToolButton:pressed { background: transparent; }"
            )

            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                normal_icon = QIcon(pixmap)
                hover_icon = QIcon(HoverIconToolButton._darken_pixmap(pixmap, alpha=90))
                button.setHoverIcons(normal_icon, hover_icon)
            else:
                # Fallback to text if asset missing
                button.setText(piece_upper)

            button.clicked.connect(lambda _checked=False, p=piece: self.promote(p))
            layout.addWidget(button)

        self.setFixedSize(
            (button_size.width() * len(pieces)) + (layout.spacing() * (len(pieces) - 1)) + layout.contentsMargins().left() + layout.contentsMargins().right(),
            button_size.height() + layout.contentsMargins().top() + layout.contentsMargins().bottom(),
        )

    def promote(self, piece):
        """Select a promotion piece and close the dialog.

        Args:
            piece (str): One of 'Q', 'R', 'B', 'N' (case-insensitive).

        Return:
            None
        """
        self.chosen_piece = self.piece_chosen_dict[piece.upper()]
        self.accept()  # Close the promotion dialog after selection    
            

class HoverIconToolButton(QToolButton):
    def __init__(self, parent=None):
        """Create a tool button that swaps icons on hover.

        Args:
            parent (QWidget | None): Optional parent widget.

        Return:
            None
        """
        super().__init__(parent)
        self._normal_icon: QIcon | None = None
        self._hover_icon: QIcon | None = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    @staticmethod
    def _darken_pixmap(pixmap: QPixmap, alpha: int = 90) -> QPixmap:
        """Return a darkened copy of a pixmap.

        Args:
            pixmap (QPixmap): Source pixmap.
            alpha (int): Darkness alpha (0-255). Higher means darker.

        Return:
            QPixmap: Darkened pixmap.
        """
        dark = QPixmap(pixmap.size())
        dark.fill(Qt.GlobalColor.transparent)

        painter = QPainter(dark)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
        painter.fillRect(dark.rect(), QColor(0, 0, 0, alpha))
        painter.end()
        return dark

    def setHoverIcons(self, normal_icon: QIcon, hover_icon: QIcon):
        """Set the icons used for normal and hover states.

        Args:
            normal_icon (QIcon): Icon displayed normally.
            hover_icon (QIcon): Icon displayed while hovering.

        Return:
            None
        """
        self._normal_icon = normal_icon
        self._hover_icon = hover_icon
        self.setIcon(normal_icon)

    def enterEvent(self, event):
        """Handle mouse enter by switching to the hover icon.
        Args:
            event: Qt enter event.
        Return:
            None
        """
        if self._hover_icon is not None:
            self.setIcon(self._hover_icon)
        return super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave by restoring the normal icon.
        Args:
            event: Qt leave event.
        Return:
            None
        """
        if self._normal_icon is not None:
            self.setIcon(self._normal_icon)
        return super().leaveEvent(event)

class SpinningGear(QWidget):
    """Spinning gear widget for animations and loading states."""
    
    def __init__(self, size=50, image_path="ui/assets/gear_icon.png"):
        """Initialize the spinning gear widget.
        
        Args:
            size (int): Size of the gear in pixels (width and height).
            image_path (str): Path to the gear image file.
        
        Return:
            None
        """
        super().__init__()
        self.setFixedSize(size, size)
        self.angle = 0
        
        # Load and scale the gear image
        original_image = QPixmap(image_path)
        self.gear_image = original_image.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_gear)
        self.timer.start(16)
    
    def rotate_gear(self):
        """Rotate the gear by a small increment.
        
        Args:
            None
        
        Return:
            None
        """
        self.angle += 2
        if self.angle >= 360:
            self.angle = 0
        self.update()
    
    def paintEvent(self, event):
        """Paint the rotating gear on the widget.
        
        Args:
            event: Qt paint event.
        
        Return:
            None
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # Move the origin to the center of the widget
        painter.translate(self.width() / 2, self.height() / 2)
        
        # Rotate the canvas
        painter.rotate(self.angle)
        
        # Draw the image centered at the origin
        offset_x = int(-self.gear_image.width() / 2)
        offset_y = int(-self.gear_image.height() / 2)
        painter.drawPixmap(offset_x, offset_y, self.gear_image)
    
    def set_image(self, image_path, size=None):
        """Update the gear image (optional method for dynamic image changes).
        
        Args:
            image_path (str): Path to the new gear image file.
            size (int | None): Optional new size. If None, keeps current size.
        
        Return:
            None
        """
        current_size = self.width() if size is None else size
        if size is not None:
            self.setFixedSize(size, size)
        
        original_image = QPixmap(image_path)
        self.gear_image = original_image.scaled(
            current_size, current_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.update()

class WinnerDialog(QDialog):
    """Dialog shown at end of game to announce winner and offer play again or quit options. 
    Quit exits the application, while play again just closes the dialog and returns to the main menu."""

    def __init__(self, winner_color="white", parent=None, reason="checkmate"):
        """Initialize the winner dialog.
        Args:
            winner_color (str): "white" or "black" indicating the winner's color.
            parent (QWidget | None): Optional parent widget.
            reason (str): "checkmate" or "timeout" indicating how the game was won
        Return:
            None
        """

        super().__init__(parent)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 225)
        self.setModal(True) 

        self.container = QFrame(self)
        self.container.setFixedSize(self.width(), self.height())
        
        # --- Updated Custom Styling (QSS) ---
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2E4C3B; /* Sleek slate blue background */
                border: 2px solid #34495e; /* Slightly lighter blue border */
                border-radius: 15px;       
            }
            QLabel {
                color: #ffffff;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50; /* Green play button */
                color: white;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#quitBtn {          
                background-color: #f44336; /* Red quit button */
            }
            QPushButton#quitBtn:hover {
                background-color: #da190b;
            }
        """)

        main_layout = QVBoxLayout(self.container)
        button_layout = QHBoxLayout()
        image_layout = QHBoxLayout()

        if reason == "checkmate":
            message = f"CHECKMATE!"
        else :
            message = f"Out of time \n{winner_color.capitalize()} wins!"

        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font = self.label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.label.setFont(font)

        self.winner_image = QPixmap(f"ui/assets/chess_assets/pieces_png/{winner_color}-king.png")
        loser_color = "black" if winner_color == "white" else "white"
        self.loser_image = QPixmap(f"ui/assets/chess_assets/pieces_png/{loser_color}-king.png")
        transform = QTransform().rotate(-90)
        self.loser_image = self.loser_image.transformed(transform, Qt.TransformationMode.SmoothTransformation)

        winner_label = QLabel()
        winner_label.setPixmap(self.winner_image)
        loser_label = QLabel()
        loser_label.setPixmap(self.loser_image)

        image_layout.addWidget(winner_label)
        image_layout.addWidget(loser_label)

        self.play_again_btn = QPushButton("Play Again")
        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setObjectName("quitBtn") 

        self.play_again_btn.clicked.connect(self.accept) 
        self.quit_btn.clicked.connect(self.reject)       

        button_layout.addWidget(self.play_again_btn)
        button_layout.addWidget(self.quit_btn)

        main_layout.addWidget(self.label)
        main_layout.addLayout(image_layout)
        main_layout.addLayout(button_layout)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.container)


class DrawDialog(QDialog):
    """Dialog shown at end of game to announce a draw and offer play again or quit options."""  

    def __init__(self, parent=None):
        """Initialize the draw dialog.
        Args:
            parent (QWidget | None): Optional parent widget.
        Return:
            None
        """
        super().__init__(parent)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(320, 225)
        self.setModal(True) 

        self.container = QFrame(self)
        self.container.setFixedSize(self.width(), self.height())
        
        # --- Updated Custom Styling (QSS) ---
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2E4C3B; /* Sleek slate blue background */
                border: 2px solid #34495e; /* Slightly lighter blue border */
                border-radius: 15px;       
            }
            QLabel {
                color: #ffffff;
                border: none;
            }
            QPushButton {
                background-color: #4CAF50; /* Green play button */
                color: white;
                border-radius: 5px;
                padding: 10px 15px;
                font-weight: bold;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton#quitBtn {          
                background-color: #f44336; /* Red quit button */
            }
            QPushButton#quitBtn:hover {
                background-color: #da190b;
            }
        """)

        main_layout = QVBoxLayout(self.container)
        button_layout = QHBoxLayout()
        image_layout = QHBoxLayout()

        message = f"DRAW"
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font = self.label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.label.setFont(font)

        self.white_image = QPixmap(f"ui/assets/chess_assets/pieces_png/white-king.png") 
        self.black_image = QPixmap(f"ui/assets/chess_assets/pieces_png/black-king.png")

        white_label = QLabel()
        white_label.setPixmap(self.white_image)
        black_label = QLabel()
        black_label.setPixmap(self.black_image)

        image_layout.addWidget(white_label)
        image_layout.addWidget(black_label)

        self.play_again_btn = QPushButton("Play Again")
        self.quit_btn = QPushButton("Quit")
        self.quit_btn.setObjectName("quitBtn") 

        self.play_again_btn.clicked.connect(self.accept) 
        self.quit_btn.clicked.connect(self.reject)       

        button_layout.addWidget(self.play_again_btn)
        button_layout.addWidget(self.quit_btn)

        main_layout.addWidget(self.label)
        main_layout.addLayout(image_layout)
        main_layout.addLayout(button_layout)

        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.container)

class WaitingDialog(QDialog):
    """Simple waiting dialog to show while path is being sent."""
    
    def __init__(self, parent=None):
        """Initialize the waiting dialog.
        Args:
            parent (QWidget | None): Optional parent widget.
        Return:
            None"""
        super().__init__(parent)
        self.setWindowTitle("Processing Move")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label = QLabel("Sending move to device...\nPlease wait.")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinning_gear = SpinningGear(65, "ui/assets/gear_icon.png")
        layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.spinning_gear, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        
        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.left() + (parent_geometry.width() - 300) // 2,
                parent_geometry.top() + (parent_geometry.height() - 100) // 2
            )

    def set_message(self, message):
        """Update the waiting message displayed in the dialog.
        Args:
            message (str): New message to display.
        Return:
            None"""
        self.label.setText(message)

class TurnIndicatorWidget(QWidget):
    """Combined widget showing current turn with dynamic background and optional waiting spinner."""
    
    def __init__(self, parent=None):
        """Initialize the turn indicator widget.
        Args:
            parent (QWidget | None): Optional parent widget.
        Return:
            None"""
        super().__init__(parent)
        self.setFixedHeight(140)
        # Allow more horizontal space for text
        self.setMinimumWidth(400)
        self.setMaximumWidth(900)
        self.current_turn = "white"  # "white" or "black"
        self.is_waiting = False
        self.waiting_message = ""
        
        # Main layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
        
        # Turn text label
        self.turn_label = QLabel("White's Turn")
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.turn_label.setStyleSheet("border: none; font-size: 32px;")
        font = self.turn_label.font()
        font.setBold(True)
        self.turn_label.setFont(font)
        
        # Container for waiting state (gear and message)
        self.waiting_container = QWidget()
        waiting_layout = QHBoxLayout(self.waiting_container)
        waiting_layout.setContentsMargins(0, 0, 0, 0)
        waiting_layout.setSpacing(15)
        
        # Spinning gear for waiting state
        self.spinning_gear = SpinningGear(70, "ui/assets/gear_icon.png")
        
        # Message label for waiting state
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.message_label.setStyleSheet("border: none; font-size: 22px")
        
        waiting_layout.addWidget(self.spinning_gear, 0, Qt.AlignmentFlag.AlignCenter)
        waiting_layout.addWidget(self.message_label, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.waiting_container.setVisible(False)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.turn_label, 1, Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.waiting_container, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Set initial background color and text color
        self.update_turn("white")
    
    def update_turn(self, color):
        """Update the turn indicator with new color (white or black).
        Args:
             color (str): "white" or "black" indicating the current player's turn.
        Return:
             None"""
        
        self.current_turn = color
        if color.lower() == "white":
            bg_color = "white"
            self.turn_label.setText("White's Turn")
        else:
            bg_color = "black"
            self.turn_label.setText("Black's Turn")
        
        # Update background color only - labels will be styled by global QSS
        self.setStyleSheet(f"""
            TurnIndicatorWidget {{
                background-color: {bg_color};
                border: 2px solid #34495e;
                border-radius: 10px;
            }}
        """)
    
    def show_waiting(self, message="Processing..."):
        """Show waiting state with spinning gear and message.
        Args :
             message (str): Message to display next to the spinning gear.
        Return :   
             None"""
        self.is_waiting = True
        self.waiting_message = message
        self.turn_label.setVisible(False)
        self.message_label.setText(message)
        self.waiting_container.setVisible(True)
    
    def hide_waiting(self):
        """Hide waiting state and show turn indicator.
        Args : 
             None
        Return :
             None"""
        self.is_waiting = False
        self.waiting_message = ""
        self.turn_label.setVisible(True)
        self.waiting_container.setVisible(False)
        self.message_label.setText("")

class InvalidMoveDialog(QDialog):
    """Dialog showing invalid move message that automatically closes after 2 seconds."""
    
    def __init__(self, parent=None):
        """Initialize the invalid move dialog.
        Args:
            parent (QWidget | None): Optional parent widget.
        Return:
            None"""
        super().__init__(parent)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(300, 150)
        self.setModal(True)
        
        self.container = QFrame(self)
        self.container.setFixedSize(self.width(), self.height())
        
        # --- Custom Styling ---
        self.container.setStyleSheet("""
            QFrame {
                background-color: #8B0000; /* Dark red background */
                border: 2px solid #FF4444; /* Red border */
                border-radius: 15px;       
            }
            QLabel {
                color: #ffffff;
                border: none;
            }
        """)
        
        main_layout = QVBoxLayout(self.container)
        
        self.label = QLabel("INVALID MOVE")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font = self.label.font()
        font.setPointSize(18)
        font.setBold(True)
        self.label.setFont(font)
        
        main_layout.addWidget(self.label)
        
        dialog_layout = QVBoxLayout(self)
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(self.container)
        
        # Timer to auto-close after 2 seconds
        self.close_timer = QTimer(self)
        self.close_timer.timeout.connect(self.reject)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(2000)  # 2000 milliseconds = 2 seconds
        
        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.left() + (parent_geometry.width() - 300) // 2,
                parent_geometry.top() + (parent_geometry.height() - 150) // 2
            )


# --- Example Usage ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = WinnerDialog(winner_color="black")
    result = dialog.exec()

    dialog = WinnerDialog(winner_color="black", reason="timeout")
    result = dialog.exec()

    dialog = WaitingDialog()
    result = dialog.exec()

    dialog = InvalidMoveDialog()
    result = dialog.exec()
