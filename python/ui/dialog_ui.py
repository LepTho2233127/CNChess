import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QWidget, QSizePolicy)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap,  QTransform, QPainter

class WinnerDialog(QDialog):
    def __init__(self, winner_color="white", parent=None, reason="checkmate"):
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

    def __init__(self, parent=None):
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
        super().__init__(parent)
        self.setWindowTitle("Processing Move")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Sending move to device...\nPlease wait.")
        self.spinning_gear = self.SpinningImageGear()
        layout.addWidget(self.label)
        layout.addWidget(self.spinning_gear)
        self.setLayout(layout)
        
        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.left() + (parent_geometry.width() - 300) // 2,
                parent_geometry.top() + (parent_geometry.height() - 100) // 2
            )

    def set_message(self, message):
        self.label.setText(message)

    class SpinningImageGear(QWidget):
        def __init__(self):
            super().__init__()
            original_image = QPixmap("ui/assets/gear_icon.png")
            self.gear_image = original_image.scaled(
            65, 65, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

            self.angle = 0

            # Animation loop
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.rotate_gear)
            self.timer.start(16) 

        def rotate_gear(self):
            self.angle += 2  
            if self.angle >= 360:
                self.angle = 0
            self.update() 

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform) # Keeps the image from looking pixelated when rotated

            # 2. Move the origin to the center of the widget
            painter.translate(self.width() / 2, self.height() / 2)

            # 3. Rotate the canvas
            painter.rotate(self.angle)

            # 4. Draw the image
            # IMPORTANT: We must offset the drawing by half the image's width and height.
            # Otherwise, the top-left corner of the image will be at the center of rotation, 
            # causing it to orbit rather than spin in place.
            offset_x = int(-self.gear_image.width() / 2)
            offset_y = int(-self.gear_image.height() / 2)
            
            painter.drawPixmap(offset_x, offset_y, self.gear_image)

class TurnIndicatorWidget(QWidget):
    """Combined widget showing current turn with dynamic background and optional waiting spinner."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        # Set a maximum and minimum width to prevent the widget from stretching when gear/message appear
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
        self.current_turn = "white"  # "white" or "black"
        self.is_waiting = False
        self.waiting_message = ""
        
        # Main layout - no stretches to prevent expansion
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        
        # Turn text label
        self.turn_label = QLabel("White's Turn")
        self.turn_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.turn_label.font()
        font.setPointSize(16)
        font.setBold(True)
        self.turn_label.setFont(font)
        
        # Spinning gear for waiting state
        self.spinning_gear = self.SpinningGear()
        self.spinning_gear.setVisible(False)
        
        # Message label for waiting state
        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setVisible(False)
        self.message_label.setMaximumWidth(250)  # Limit width to prevent stretching
        self.message_label.setMinimumHeight(40)
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        font = self.message_label.font()
        font.setPointSize(10)
        self.message_label.setFont(font)
        
        # Add widgets to layout - centered with limited expansion
        self.main_layout.addWidget(self.turn_label, 1, Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.spinning_gear, 0, Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.message_label, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Set initial background color and text color
        self.update_turn("white")
    
    def update_turn(self, color):
        """Update the turn indicator with new color (white or black)."""
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
        """Show waiting state with spinning gear and message."""
        self.is_waiting = True
        self.waiting_message = message
        self.turn_label.setVisible(False)
        self.spinning_gear.setVisible(True)
        self.message_label.setText(message)
        self.message_label.setVisible(True)
    
    def hide_waiting(self):
        """Hide waiting state and show turn indicator."""
        self.is_waiting = False
        self.waiting_message = ""
        self.turn_label.setVisible(True)
        self.spinning_gear.setVisible(False)
        self.message_label.setVisible(False)
        self.message_label.setText("")
    
    class SpinningGear(QWidget):
        """Spinning gear widget for waiting state."""
        
        def __init__(self):
            super().__init__()
            self.setFixedSize(50, 50)
            original_image = QPixmap("ui/assets/gear_icon.png")
            self.gear_image = original_image.scaled(
                50, 50, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            self.angle = 0
            
            # Animation timer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.rotate_gear)
            self.timer.start(16)
        
        def rotate_gear(self):
            self.angle += 2
            if self.angle >= 360:
                self.angle = 0
            self.update()
        
        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            painter.translate(self.width() / 2, self.height() / 2)
            painter.rotate(self.angle)
            
            offset_x = int(-self.gear_image.width() / 2)
            offset_y = int(-self.gear_image.height() / 2)
            painter.drawPixmap(offset_x, offset_y, self.gear_image)

# --- Example Usage ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = WinnerDialog(winner_color="black")
    result = dialog.exec()

    dialog = WinnerDialog(winner_color="black", reason="timeout")
    result = dialog.exec()

    dialog = WaitingDialog()
    result = dialog.exec()
