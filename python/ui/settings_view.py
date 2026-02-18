from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QSlider, QPushButton, QDoubleSpinBox, QApplication,
                             QStyleOption, QStyle)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPainter
import sys

class SettingsView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        grid = self.build_grid()
        layout_coord = self.build_coord()
        layout_remoteXY = self.build_remoteXY()
        layout_controls = self.build_controls()
        layout_speed = self.build_speed()

        coord_layout = QVBoxLayout()
        coord_layout.addWidget(grid)
        coord_layout.addLayout(layout_coord)
        coord_layout.addLayout(layout_remoteXY)
        coord_layout.addLayout(layout_controls)
        left_layout = QHBoxLayout()
        left_layout.addLayout(coord_layout)
        left_layout.addLayout(layout_speed)
        camera_layout = self.build_camera()
        
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(camera_layout)

        self.setLayout(main_layout)

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

        layout = QHBoxLayout()
        layout.addWidget(X_spinner)
        layout.addWidget(y_spinner)
        layout.addWidget(go_button)

        return layout
    
    def build_speed(self):

        speed_label = QLabel("Speed : 50%", self)

        speed_slider = QSlider(self)
        speed_slider.setOrientation(Qt.Orientation.Vertical)
        speed_slider.setRange(0, 100)
        speed_slider.setValue(50)
        speed_slider.valueChanged.connect(lambda value: speed_label.setText(f"Speed : {value}%"))

        layout = QVBoxLayout()
        layout.addWidget(speed_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(speed_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

        return layout
    
    def build_grid(self):
        grid = GridView()
        return grid

    def build_camera(self):
        footage = QPushButton("Camera Footage", self)
        footage.setFixedSize(400, 300)

        pic_button = QPushButton("Take Picture", self)
        pic_button.clicked.connect(self.take_picture)

        layout = QVBoxLayout()
        layout.addWidget(footage)
        layout.addWidget(pic_button)

        return layout

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

    def take_picture(self):
        print("take picture")

class GridView(QWidget):

    grid_width_mm = 431.8
    grid_height_mm = 406.4
    x = 0
    y = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init()

    def init(self):
        self.setFixedSize(int(self.grid_width_mm), int(self.grid_height_mm))
        self.setStyleSheet("background-color: white; border: 1px solid black;")
    
    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)
        p.end()
        
    def mousePressEvent(self, event):
        self.x = int(event.position().x())
        self.y = int(event.position().y())

        print(f"Clicked at: ({self.x}, {self.y})")
    
    def get_coord(self):
        return self.x, self.y


if __name__ == "__main__":

    app = QApplication(sys.argv)
    settings_view = SettingsView()
    settings_view.show()
    sys.exit(app.exec())