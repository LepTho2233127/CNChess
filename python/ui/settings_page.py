from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QSlider, QPushButton, QDoubleSpinBox, QApplication,
                             QStyleOption, QStyle)
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPixmap
import sys
import os

class SettingsView(QWidget):

    grid_width_mm = 431.8
    grid_height_mm = 406.4

    def __init__(self, com=None):
        super().__init__()
        self._updating_spinners = False
        self.controller = SettingsController(self, com)
        self.init_ui()

    def init_ui(self):
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.controller.quit)
        back_button.setFixedSize(80, 30)
        # layout_speed = self.build_speed()
        grid = self.build_grid()
        layout_coord = self.build_coord()
        layout_remoteXY = self.build_remoteXY()
        layout_controls = self.build_controls()
        camera_layout = self.build_camera()

        left_layout = QVBoxLayout()
        left_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignTop)
        # left_layout.addLayout(layout_speed)
        middle_layout = QVBoxLayout()
        middle_layout.addWidget(grid, alignment=Qt.AlignmentFlag.AlignHCenter)
        middle_layout.addLayout(layout_coord)
        middle_layout.addLayout(layout_remoteXY)
        middle_layout.addLayout(layout_controls)
        
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addLayout(middle_layout)
        main_layout.addLayout(camera_layout)
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 2)
        main_layout.setStretch(2, 2)

        self.setLayout(main_layout)

    def build_remoteXY(self):

        up_button = QPushButton("+Y", self)
        up_button.clicked.connect(self.move_up)

        down_button = QPushButton("-Y", self)
        down_button.clicked.connect(self.move_down)

        left_button = QPushButton("-X", self)
        left_button.clicked.connect(self.move_left)

        right_button = QPushButton("+X", self)
        right_button.clicked.connect(self.move_right)

        self.step_spinner = QDoubleSpinBox(self)
        self.step_spinner.setRange(0.0, 100.0)
        self.step_spinner.setSingleStep(1.0)
        self.step_spinner.setValue(5.0)
        self.step_spinner.setSuffix(" mm")

        z_up_button = QPushButton("+Z", self)
        z_up_button.clicked.connect(self.controller.z_move_up)
        z_down_button = QPushButton("-Z", self)
        z_down_button.clicked.connect(self.controller.z_move_down)

        grid_layout = QGridLayout()
        grid_layout.addWidget(up_button, 0, 1)
        grid_layout.addWidget(down_button, 2, 1)
        grid_layout.addWidget(left_button, 1, 0)
        grid_layout.addWidget(right_button, 1, 2)
        grid_layout.addWidget(self.step_spinner, 1, 1)

        vbox_layout = QVBoxLayout()
        vbox_layout.addWidget(z_up_button)
        vbox_layout.addWidget(z_down_button)

        layout = QHBoxLayout()
        layout.addLayout(grid_layout)
        layout.addLayout(vbox_layout)

        return layout

    def build_controls(self):

        home_button = QPushButton("HOME", self)
        home_button.clicked.connect(self.controller.home)

        stop_button = QPushButton("STOP", self)
        stop_button.clicked.connect(self.controller.stop)

        layout = QVBoxLayout()
        layout.addWidget(home_button)
        layout.addWidget(stop_button)

        return layout
    
    def build_coord(self):

        self.x_spinner = QDoubleSpinBox(self)
        self.x_spinner.setRange(0.0, self.grid_width_mm)
        self.x_spinner.setSingleStep(1.0)
        self.x_spinner.setValue(0.0)
        self.x_spinner.setPrefix("X: ")
        self.x_spinner.valueChanged.connect(self.on_spinner_changed)

        self.y_spinner = QDoubleSpinBox(self)
        self.y_spinner.setRange(0.0, self.grid_height_mm)
        self.y_spinner.setSingleStep(1.0)
        self.y_spinner.setValue(0.0)
        self.y_spinner.setPrefix("Y: ")
        self.y_spinner.valueChanged.connect(self.on_spinner_changed)

        go_button = QPushButton("GO", self)
        go_button.clicked.connect(self.controller.go)

        layout = QHBoxLayout()
        layout.addWidget(self.x_spinner)
        layout.addWidget(self.y_spinner)
        layout.addWidget(go_button)

        return layout
    
    # def build_speed(self):

    #     self.speed_label = QLabel("Speed : 50%", self)
    #     self.speed_label.setFixedHeight(100)

    #     speed_slider = QSlider(self)
    #     speed_slider.setOrientation(Qt.Orientation.Vertical)
    #     speed_slider.setRange(0, 100)
    #     speed_slider.setValue(50)
    #     speed_slider.setFixedSize(25, 400)
    #     speed_slider.valueChanged.connect(self.update_speed)

    #     layout = QVBoxLayout()
    #     layout.addWidget(self.speed_label, alignment=Qt.AlignmentFlag.AlignHCenter)
    #     layout.addWidget(speed_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

    #     return layout
    
    def build_grid(self):
        self.grid = GridView()
        self.grid.positionChanged.connect(self.update_coord)
        return self.grid

    def build_camera(self):
        last_pic = QLabel(self)
        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'temp_img.jpg')

        last_pic.setPixmap(QPixmap(img_path))
        last_pic.setFixedSize(400, 300)

        pic_button = QPushButton("Take Picture", self)
        pic_button.clicked.connect(self.controller.take_picture)

        layout = QVBoxLayout()
        layout.addWidget(last_pic, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(pic_button)

        return layout

    def update_coord(self, x, y):
        self._updating_spinners = True
        self.x_spinner.setValue(float(x))
        self.y_spinner.setValue(abs(float(y)-self.grid_height_mm))
        self._updating_spinners = False
        self.grid.update_dot(x, y)
    
    def on_spinner_changed(self):
        if self._updating_spinners:
            return
        x = self.x_spinner.value()
        y = abs(self.y_spinner.value() - self.grid_height_mm)
        self.grid.update_dot(x, y)

    def move_up(self):
        current_value = abs(self.y_spinner.value() - self.grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value - self.step_spinner.value())

    def move_down(self):
        current_value = abs(self.y_spinner.value() - self.grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value + self.step_spinner.value())
    
    def move_left(self):
        current_value = self.x_spinner.value()
        self.update_coord(current_value - self.step_spinner.value(), abs(self.y_spinner.value() - self.grid_height_mm))
    
    def move_right(self):
        current_value = self.x_spinner.value()
        self.update_coord(current_value + self.step_spinner.value(), abs(self.y_spinner.value() - self.grid_height_mm))

class SettingsController(QObject):

    game_page_signal = pyqtSignal(bool)

    def __init__(self, view, com):
        super().__init__()
        self.view = view
        self.com = com

    def quit(self):
        self.game_page_signal.emit(True)

    def go(self):
        self.com.send_position(self.view.x_spinner.value(), self.view.y_spinner.value())

    def home(self):
        self.com.go_home()

    def stop(self):
        self.com.stop()

    def z_move_up(self):
        self.com.move_servo(True)

    def z_move_down(self):
        self.com.move_servo(False)

    # def update_speed(self, value):
    #     self.speed_label.setText(f"Speed : {value}%")
    #     print(f"Speed set to {value}%")
    
    def take_picture(self):
        print("take picture")

class GridView(QWidget):

    grid_width_mm = 431.8
    grid_height_mm = 406.4
    x = 0
    y = 0

    positionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init()

    def init(self):
        self.setFixedSize(int(self.grid_width_mm), int(self.grid_height_mm))
        self.setStyleSheet("background-color: white; border: 1px solid black;")

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, painter, self)
        pen = QPen(Qt.GlobalColor.red, 5)
        painter.setPen(pen)
        painter.drawPoint(int(getattr(self, 'x', 0)), int(getattr(self, 'y', 0)))
        painter.end()

    def mousePressEvent(self, event):
        self.x = int(event.position().x())
        self.y = int(event.position().y())
        self.positionChanged.emit(self.x, self.y)

    def update_dot(self, x, y):
        self.x = x
        self.y = y
        self.update()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    settings_view = SettingsView()
    settings_view.show()
    sys.exit(app.exec())