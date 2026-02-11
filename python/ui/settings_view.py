from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QSlider, QPushButton, QDoubleSpinBox, QApplication, QGraphicsView
from PyQt6.QtCore import Qt
import sys

class SettingsView(QWidget):

    width_mm = 431.8
    height_mm = 406.4

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = self.build_speed()
        self.setLayout(layout)

    def build_remoteXY(self):

        up_button = QPushButton("▲", self)
        up_button.clicked.connect(self.move_up)

        down_button = QPushButton("▼", self)
        down_button.clicked.connect(self.move_down)

        left_button = QPushButton("◄", self)
        left_button.clicked.connect(self.move_left)

        right_button = QPushButton("►", self)
        right_button.clicked.connect(self.move_right)

        step_spinner = QDoubleSpinBox(self)
        step_spinner.setRange(0.0, 100.0)
        step_spinner.setSingleStep(1.0)
        step_spinner.setValue(5.0)
        step_spinner.setSuffix(" mm")

        layout = QGridLayout()
        layout.addWidget(up_button, 0, 1)
        layout.addWidget(down_button, 2, 1)
        layout.addWidget(left_button, 1, 0)
        layout.addWidget(right_button, 1, 2)
        layout.addWidget(step_spinner, 1, 1)

        return layout

    def build_controls(self):

        home_button = QPushButton("HOME", self)
        home_button.clicked.connect(self.home)

        stop_button = QPushButton("STOP", self)
        stop_button.clicked.connect(self.stop)

        layout = QVBoxLayout()
        layout.addWidget(home_button)
        layout.addWidget(stop_button)

        return layout
    
    def build_coord(self):

        X_spinner = QDoubleSpinBox(self)
        X_spinner.setRange(0.0, 400.0)
        X_spinner.setSingleStep(1.0)
        X_spinner.setValue(0.0)
        X_spinner.setPrefix("X: ")

        y_spinner = QDoubleSpinBox(self)
        y_spinner.setRange(0.0, 400.0)
        y_spinner.setSingleStep(1.0)
        y_spinner.setValue(0.0)
        y_spinner.setPrefix("Y: ")

        go_button = QPushButton("GO", self)
        go_button.clicked.connect(self.go)

        controls_layout = self.build_controls()

        layout = QHBoxLayout()
        layout.addWidget(X_spinner)
        layout.addWidget(y_spinner)
        layout.addWidget(go_button)
        layout.addLayout(controls_layout)

        return layout
    
    def build_speed(self):

        speed_label = QLabel("Speed", self)

        speed_slider = QSlider(self)
        speed_slider.setOrientation(Qt.Orientation.Vertical)
        speed_slider.setRange(0, 100)
        speed_slider.setValue(50)

        layout = QVBoxLayout()
        layout.addWidget(speed_label)
        layout.addWidget(speed_slider)

        return layout
    
    def build_grid(self):
        pass
        # canvas = GridView()

    def go(self):
        print("go")

    def home(self):
        print("home")

    def stop(self):
        print("stop")

    def move_up(self):
        print("move up")

    def move_down(self):
        print("move down") 
    
    def move_left(self):
        print("move left")
    
    def move_right(self):
        print("move right")

# class GridView(QGraphicsView):

if __name__ == "__main__":

    app = QApplication(sys.argv)
    settings_view = SettingsView()
    settings_view.show()
    sys.exit(app.exec())