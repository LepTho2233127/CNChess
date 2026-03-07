import sys
from PyQt6.QtWidgets import (QApplication, QDialog, QLabel, 
                             QPushButton, QVBoxLayout, QHBoxLayout, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap,  QTransform

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

# --- Example Usage ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = CheckmateDialog(winner_color="black")
    result = dialog.exec()
