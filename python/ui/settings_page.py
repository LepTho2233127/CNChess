from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QSlider, QPushButton, QDoubleSpinBox, QApplication,
                             QStyleOption, QStyle)
from PyQt6.QtCore import QLine, QPoint, Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QPainter, QPen, QPixmap
from Control import Position
from ui.dialog_ui import WaitingDialog

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from Control import Position
import cv2 


SQUARE_SIZE_MM = 50.8
grid_width_mm = 8*SQUARE_SIZE_MM
grid_height_mm = 8*SQUARE_SIZE_MM

class SendPositionWorker(QObject):
    """Worker thread to send position commands without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, communication, position):
        super().__init__()
        self.communication = communication
        self.position = position
    
    def run(self):
        """Execute send_position in the worker thread."""
        try:
            self.communication.send_position(self.position, relative=False)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SendHomeWorker(QObject):
    """Worker thread to send home command without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, communication):
        super().__init__()
        self.communication = communication
    
    def run(self):
        """Execute go_home in the worker thread."""
        try:
            self.communication.go_home()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SettingsView(QWidget):

    def __init__(self, com=None, cam=None):
        super().__init__()
        self._updating_spinners = False
        self.controller = SettingsController(self, com, cam)
        self.init_ui()
    
    def cleanup_threads(self):
        """Clean up all worker threads in the settings page."""
        self.controller.cleanup_threads()

    def init_ui(self):
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.controller.quit)
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
        # Removed setAlignment for QSS control

        return layout
    
    def build_coord(self):

        self.x_spinner = QDoubleSpinBox(self)
        self.x_spinner.setRange(0.0, grid_width_mm)
        self.x_spinner.setSingleStep(1.0)
        self.x_spinner.setValue(0.0)
        self.x_spinner.setPrefix("X: ")
        self.x_spinner.valueChanged.connect(self.on_spinner_changed)

        self.y_spinner = QDoubleSpinBox(self)
        self.y_spinner.setRange(0.0, grid_height_mm)
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
        self.last_pic = QLabel(self)
        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')

        image = QPixmap(img_path)
        if not image.isNull():
            image = image.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        self.last_pic.setPixmap(image)

        pic_button = QPushButton("TAKE PICTURE", self)
        pic_button.clicked.connect(self.controller.take_picture)

        layout = QVBoxLayout()
        layout.addWidget(self.last_pic)
        layout.addWidget(pic_button)

        return layout

    def update_coord(self, x, y, computer_move=False):
        self.view_updating_spinners = True
        self.x_spinner.setValue(float(x))
        if not computer_move:
            self.y_spinner.setValue(grid_height_mm - float(y))
           
        else :
            self.y_spinner.setValue(y)     
            y = grid_height_mm - float(y)
        
        self._updating_spinners = False
        self.grid.update_dot(x, y)
    
    def on_spinner_changed(self):
        if self._updating_spinners:
            return
        x = self.x_spinner.value()
        y = abs(self.y_spinner.value() - grid_height_mm)
        self.grid.update_dot(x, y)

    def move_up(self):
        current_value = abs(self.y_spinner.value() - grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value - self.step_spinner.value())

    def move_down(self):
        current_value = abs(self.y_spinner.value() - grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value + self.step_spinner.value())
    
    def move_left(self):
        current_value = self.x_spinner.value()
        self.update_coord(current_value - self.step_spinner.value(), abs(self.y_spinner.value() - grid_height_mm))
    
    def move_right(self):
        current_value = self.x_spinner.value()
        self.update_coord(current_value + self.step_spinner.value(), abs(self.y_spinner.value() - grid_height_mm))

class SettingsController(QObject):

    game_page_signal = pyqtSignal(bool)

    def __init__(self, view, com, cam):
        super().__init__()
        self.view = view
        self.com = com
        self.cam = cam
        
        # Initialize worker thread and waiting dialog
        self.send_position_worker = None
        self.send_position_thread = None
        self.send_home_worker = None
        self.send_home_thread = None
        self.waiting_dialog = WaitingDialog(self.view)
        self.active_operations = 0  # Counter to track concurrent operations

    def cleanup_threads(self):
        """Clean up all worker threads in the controller."""
        if self.send_position_thread is not None:
            if self.send_position_thread.isRunning():
                print("[INFO] Stopping send_position thread...")
                self.send_position_thread.quit()
                self.send_position_thread.wait()
            self.send_position_thread = None
            self.send_position_worker = None
        
        if self.send_home_thread is not None:
            if self.send_home_thread.isRunning():
                print("[INFO] Stopping send_home thread...")
                self.send_home_thread.quit()
                self.send_home_thread.wait()
            self.send_home_thread = None
            self.send_home_worker = None
    
    def quit(self):
        self.cleanup_threads()
        self.game_page_signal.emit(True)

    def send_position_async(self, position):
        """Send position to device asynchronously without blocking the UI."""
        # Wait for any previous thread to finish before starting a new one
        if self.send_position_thread is not None and self.send_position_thread.isRunning():
            self.send_position_thread.quit()
            self.send_position_thread.wait()

        # Create worker and thread
        self.send_position_worker = SendPositionWorker(self.com, position)
        self.send_position_thread = QThread(parent=self)
        self.send_position_worker.moveToThread(self.send_position_thread)
        
        # Connect signals
        self.send_position_thread.started.connect(self.send_position_worker.run)
        self.send_position_worker.finished.connect(self.on_send_position_finished)
        self.send_position_worker.finished.connect(self.send_position_thread.quit)
        self.send_position_worker.error.connect(self.on_send_position_error)
        self.send_position_worker.error.connect(self.send_position_thread.quit)
        
        # Show waiting dialog and start thread
        self.active_operations += 1
        self.waiting_dialog.set_message("Sending position to device...\nPlease wait.")
        self.waiting_dialog.show()
        self.send_position_thread.start()

    def on_send_position_finished(self):
        """Handler when send_position completes successfully."""
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()

    def on_send_position_error(self, error_msg):
        """Handler when send_position encounters an error."""
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()
        print(f"Error sending position: {error_msg}")

    def go(self):
        pos = Position(float(self.view.x_spinner.value() + 0.5*SQUARE_SIZE_MM), float(self.view.y_spinner.value()+0.5*SQUARE_SIZE_MM))
        self.send_position_async(pos)

    def send_home_async(self):
        """Send home command to device asynchronously without blocking the UI."""
        # Wait for any previous thread to finish before starting a new one
        if self.send_home_thread is not None and self.send_home_thread.isRunning():
            self.send_home_thread.quit()
            self.send_home_thread.wait()

        # Create worker and thread
        self.send_home_worker = SendHomeWorker(self.com)
        self.send_home_thread = QThread(parent=self)
        self.send_home_worker.moveToThread(self.send_home_thread)
        
        # Connect signals
        self.send_home_thread.started.connect(self.send_home_worker.run)
        self.send_home_worker.finished.connect(self.on_send_home_finished)
        self.send_home_worker.finished.connect(self.send_home_thread.quit)
        self.send_home_worker.error.connect(self.on_send_home_error)
        self.send_home_worker.error.connect(self.send_home_thread.quit)
        
        # Show waiting dialog and start thread
        self.active_operations += 1
        self.waiting_dialog.set_message("Sending home command...\nPlease wait.")
        self.waiting_dialog.show()
        self.send_home_thread.start()

    def on_send_home_finished(self):
        """Handler when send_home completes successfully."""
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()

    def on_send_home_error(self, error_msg):
        """Handler when send_home encounters an error."""
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()
        print(f"Error sending home command: {error_msg}")

    def home(self):
        self.send_home_async()

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
        image = self.cam.process_image()["warped_image"]
        display_image_with_grid = self.cam.squares.draw_grid(image, color=(0, 255, 0), thickness=2)

        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')
        cv2.imwrite(img_path, cv2.cvtColor(display_image_with_grid, cv2.COLOR_RGB2BGR))

        image = QPixmap(img_path)
        image = image.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)

        self.view.last_pic.setPixmap(image)
        
class GridView(QWidget):

    x = 0
    y = grid_height_mm

    positionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init()

    def init(self):
        self.setFixedSize(int(grid_width_mm), int(grid_height_mm))
        self.setStyleSheet("background-color: black; border: 2px solid white;")

    def paintEvent(self, event):
        painter = QPainter(self)
        # Paint background
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        
        # Paint border
        border_pen = QPen(Qt.GlobalColor.white, 2)
        painter.setPen(border_pen)
        painter.drawRect(0, 0, self.width() - 1, self.height() - 1)
        
        # Paint grid lines
        grid_pen = QPen(Qt.GlobalColor.white, 1)
        painter.setPen(grid_pen)
        for i in range(0, round(grid_width_mm), round(grid_width_mm/8.0)):
            start_point = QPoint(i, 0)
            end_point = QPoint(i, round(grid_height_mm))
            v_line = QLine(start_point, end_point)
            painter.drawLine(v_line)
        for j in range(0, round(grid_height_mm), round(grid_height_mm/8.0)):
            start_point = QPoint(0, j)
            end_point = QPoint(round(grid_width_mm), j)
            h_line = QLine(start_point, end_point)
            painter.drawLine(h_line)
        
        # Paint the red dot for current position
        dot_pen = QPen(Qt.GlobalColor.red, 6)
        painter.setPen(dot_pen)
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
    # Load QSS theme for standalone testing
    qss_path = os.path.join(os.path.dirname(__file__), "cnchess_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: QSS theme file not found at {qss_path}")
    settings_view = SettingsView()
    settings_view.show()
    sys.exit(app.exec())