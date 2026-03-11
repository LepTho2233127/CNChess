import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap,  QTransform, QPainter

class CheckmateDialog(QDialog):
    def __init__(self, winner_color="white", parent=None):
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

        message = f"CHECKMATE!"
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        font = self.label.font()
        font.setPointSize(18)
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
        label = QLabel("Sending move to device...\nPlease wait.")
        self.spinning_gear = self.SpinningImageGear()
        layout.addWidget(label)
        layout.addWidget(self.spinning_gear)
        self.setLayout(layout)
        
        # Center the dialog on parent
        if parent:
            parent_geometry = parent.geometry()
            self.move(
                parent_geometry.left() + (parent_geometry.width() - 300) // 2,
                parent_geometry.top() + (parent_geometry.height() - 100) // 2
            )
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

# --- Example Usage ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CheckmateDialog(winner_color="black")
    result = dialog.exec()

    dialog = WaitingDialog()
    result = dialog.exec()
