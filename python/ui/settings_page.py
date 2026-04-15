import os
import sys
import cv2 
import threading

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QLabel, QPushButton, QDoubleSpinBox, QApplication)
from PyQt6.QtCore import QLine, QPoint, Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QPainter, QPen, QPixmap

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from ui.dialog_ui import WaitingDialog
from Control import Position

SQUARE_SIZE_MM = 50.8
grid_width_mm = 8*SQUARE_SIZE_MM
grid_height_mm = 8*SQUARE_SIZE_MM

class SendPositionWorker(QObject):
    """Worker thread to send position commands without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, communication, position):
        """Initialize worker with communication and target position.
        
        Args:
            communication: Communication instance for sending commands.
            position (Position): Target position to send.
        
        Return:
            None
        """
        super().__init__()
        self.communication = communication
        self.position = position
        self._stop_event = threading.Event()

    def cancel(self):
        self._stop_event.set()
    
    def run(self):
        """Execute send_position in the worker thread."""
        try:
            if self._stop_event.is_set():
                return
            self.communication.send_position(self.position, relative=False, stop_event=self._stop_event)
            if self._stop_event.is_set():
                return
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SendHomeWorker(QObject):
    """Worker thread to send home command without blocking the UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, communication):
        """Initialize worker with communication instance.
        
        Args:
            communication: Communication instance for sending commands.
        
        Return:
            None
        """
        super().__init__()
        self.communication = communication
        self._stop_event = threading.Event()

    def cancel(self):
        """Cancel current home operation.
        
        Args:
            None
        
        Return:
            None
        """
        self._stop_event.set()

    def run(self):
        """Execute go_home in the worker thread.

        Args:
            None

        Return:
            None
        """
        try:
            if self._stop_event.is_set():
                return
            self.communication.go_home(stop_event=self._stop_event)
            if self._stop_event.is_set():
                return
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

class SettingsView(QWidget):

    def __init__(self, com=None, cam=None):
        """Initialize settings view with communication and camera instances.
        
        Args:
            com: Communication instance for device control.
            cam: Camera instance for image capture.
        
        Return:
            None
        """
        super().__init__()
        self._updating_spinners = False
        self.controller = SettingsController(self, com, cam)
        self.init_ui()
    
    def cleanup_threads(self):
        """Clean up all worker threads in the settings page."""
        self.controller.cleanup_threads()

    def init_ui(self):
        """Initialize settings page UI layout.
        
        Args:
            None
        
        Return:
            None
        """
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.controller.quit)
        grid = self.build_grid()
        layout_coord = self.build_coord()
        layout_remoteXY = self.build_remoteXY()
        layout_controls = self.build_controls()
        camera_layout = self.build_camera()

        left_layout = QVBoxLayout()
        left_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignTop)
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
        """Build XY axis manual movement control panel.
        
        Args:
            None
        
        Return:
            QHBoxLayout: Layout containing movement buttons and step control.
        """
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
        """Build home and stop control buttons.
        
        Args:
            None
        
        Return:
            QVBoxLayout: Layout containing HOME and STOP buttons.
        """
        home_button = QPushButton("HOME", self)
        home_button.clicked.connect(self.controller.home)

        stop_button = QPushButton("STOP", self)
        stop_button.clicked.connect(self.controller.stop)

        layout = QVBoxLayout()
        layout.addWidget(home_button)
        layout.addWidget(stop_button)

        return layout
    
    def build_coord(self):
        """Build coordinate input spinners and GO button.
        
        Args:
            None
        
        Return:
            QHBoxLayout: Layout containing X/Y spinners and GO button.
        """
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
    
    def build_grid(self):
        """Build grid display widget.
        
        Args:
            None
        
        Return:
            GridView: Grid visualization widget.
        """
        self.grid = GridView()
        self.grid.positionChanged.connect(self.update_coord)
        return self.grid

    def build_camera(self):
        """Build camera display and calibration section.
        
        Args:
            None
        
        Return:
            QVBoxLayout: Layout containing camera image and control buttons.
        """
        self.last_pic = QLabel(self)
        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')

        image = QPixmap(img_path)
        if not image.isNull():
            image = image.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)
        self.last_pic.setPixmap(image)

        pic_button = QPushButton("TAKE PICTURE", self)
        pic_button.clicked.connect(self.controller.take_picture)
        pic_button.setObjectName("camera_button")

        calib_button = QPushButton("CALIBRATE CAMERA", self)
        calib_button.clicked.connect(self.controller.calibrate_camera)
        calib_button.setObjectName("camera_button")

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.last_pic, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(20)
        layout.addWidget(pic_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(calib_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

        return layout

    def update_coord(self, x, y, computer_move=False):
        """Update coordinate spinners and grid position indicator.
        
        Args:
            x (float): X coordinate value.
            y (float): Y coordinate value.
            computer_move (bool): Whether this is a computer move (affects Y transformation).
        
        Return:
            None
        """
        self.view_updating_spinners = True
        self.x_spinner.setValue(float(x))
        if not computer_move:
            self.y_spinner.setValue(grid_height_mm - float(y))
           
        else :
            self.y_spinner.setValue(y)     
            y = grid_height_mm - float(y)
            x = x - SQUARE_SIZE_MM/2
            y = y - SQUARE_SIZE_MM/2 + SQUARE_SIZE_MM
        
        self._updating_spinners = False
        self.grid.update_dot(x,y)
    
    def on_spinner_changed(self):
        """Handle coordinate spinner value changes.
        
        Args:
            None
        
        Return:
            None
        """
        if self._updating_spinners:
            return
        x = self.x_spinner.value()
        y = abs(self.y_spinner.value() - grid_height_mm)
        self.grid.update_dot(x, y)

    def move_up(self):
        """Move gantry up (increase Y coordinate).
        
        Args:
            None
        
        Return:
            None
        """
        current_value = abs(self.y_spinner.value() - grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value - self.step_spinner.value())

    def move_down(self):
        """Move gantry down (decrease Y coordinate).
        
        Args:
            None
        
        Return:
            None
        """
        current_value = abs(self.y_spinner.value() - grid_height_mm)
        self.update_coord(self.x_spinner.value(), current_value + self.step_spinner.value())
    
    def move_left(self):
        """Move gantry left (decrease X coordinate).
        
        Args:
            None
        
        Return:
            None
        """
        current_value = self.x_spinner.value()
        self.update_coord(current_value - self.step_spinner.value(), abs(self.y_spinner.value() - grid_height_mm))
    
    def move_right(self):
        """Move gantry right (increase X coordinate).
        
        Args:
            None
        
        Return:
            None
        """
        current_value = self.x_spinner.value()
        self.update_coord(current_value + self.step_spinner.value(), abs(self.y_spinner.value() - grid_height_mm))

    def update_captured_image(self, img_path=os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')):
        """Take picture and update image in view.
        
        Args:
            img_path (str): File path to new image.
        
        Return:
            None
        """
        self.controller.update_picture(img_path=img_path)

class SettingsController(QObject):

    back_button_signal = pyqtSignal()

    def __init__(self, view, com, cam):
        """Initialize settings controller with view and hardware instances.
        
        Args:
            view (SettingsView): Settings view widget.
            com: Communication instance for device control.
            cam: Camera instance for image capture.
        
        Return:
            None
        """
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
        self._is_shutting_down = False

    def cleanup_threads(self):
        """Clean up all worker threads in the controller."""
        self._is_shutting_down = True
        self.waiting_dialog.hide()

        if self.send_position_thread is not None:
            if self.send_position_worker is not None:
                self.send_position_worker.cancel()
            if self.send_position_thread.isRunning():
                print("[INFO] Stopping send_position thread...")
                self.send_position_thread.quit()
                self.send_position_thread.wait(2000)
            self.send_position_thread = None
            self.send_position_worker = None
        
        if self.send_home_thread is not None:
            if self.send_home_worker is not None:
                self.send_home_worker.cancel()
            if self.send_home_thread.isRunning():
                print("[INFO] Stopping send_home thread...")
                self.send_home_thread.quit()
                self.send_home_thread.wait(2000)
            self.send_home_thread = None
            self.send_home_worker = None
    
    def quit(self):
        """Cleanup and emit back button signal to return to previous page.
        
        Args:
            None
        
        Return:
            None
        """
        self.cleanup_threads()
        self.back_button_signal.emit()

    def send_position_async(self, position):
        """Send position to device asynchronously without blocking the UI."""
        if self._is_shutting_down:
            return

        # Wait for any previous thread to finish before starting a new one
        if self.send_position_thread is not None and self.send_position_thread.isRunning():
            if self.send_position_worker is not None:
                self.send_position_worker.cancel()
            self.send_position_thread.quit()
            self.send_position_thread.wait(2000)

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
        if self._is_shutting_down:
            return
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()

    def on_send_position_error(self, error_msg):
        """Handler when send_position encounters an error."""
        if self._is_shutting_down:
            return
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
        if self._is_shutting_down:
            return

        # Wait for any previous thread to finish before starting a new one
        if self.send_home_thread is not None and self.send_home_thread.isRunning():
            if self.send_home_worker is not None:
                self.send_home_worker.cancel()
            self.send_home_thread.quit()
            self.send_home_thread.wait(2000)

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
        if self._is_shutting_down:
            return
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()

    def on_send_home_error(self, error_msg):
        """Handler when send_home encounters an error."""
        if self._is_shutting_down:
            return
        self.active_operations -= 1
        if self.active_operations <= 0:
            self.active_operations = 0
            self.waiting_dialog.hide()
        print(f"Error sending home command: {error_msg}")

    def home(self):
        """Home the gantry to origin position.
        
        Args:
            None
        
        Return:
            None
        """
        self.view.x_spinner.setValue(0.0)
        self.view.y_spinner.setValue(0.0)
        self.send_home_async()

    def stop(self):
        """Stop the gantry motor immediately.
        
        Args:
            None
        
        Return:
            None
        """
        self.com.stop()

    def z_move_up(self):
        """Move servo magnet up.
        
        Args:
            None
        
        Return:
            None
        """
        self.com.move_servo(True)

    def z_move_down(self):
        """Move servo magnet down.
        
        Args:
            None
        
        Return:
            None
        """
        self.com.move_servo(False)

    # def update_speed(self, value):
    #     self.speed_label.setText(f"Speed : {value}%")
    #     print(f"Speed set to {value}%")
    
    def take_picture(self):
        """Capture image from camera and display it.
        
        Args:
            None
        
        Return:
            None
        """
        image = self.cam.process_image()["warped_image"]
        display_image_with_grid = self.cam.squares.draw_grid(image, color=(0, 255, 0), thickness=2)

        img_path = os.path.join(os.path.dirname(__file__), 'assets', 'captured_image.jpg')
        cv2.imwrite(img_path, cv2.cvtColor(display_image_with_grid, cv2.COLOR_RGB2BGR))

        self.update_picture(img_path)
    
    def update_picture(self, img_path):
        """Update camera image display with new image.
        
        Args:
            image: New image to display.
        
        Return:
            None
        """
        pixmap = QPixmap(img_path)
        pixmap = pixmap.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)

        self.view.last_pic.setPixmap(pixmap)

    def calibrate_camera(self):
        """Launch camera calibration from UI.
        
        Args:
            None
        
        Return:
            None
        """
        self.cam.recalibrate_from_UI()
        
class GridView(QWidget):
    """Grid visualization widget for gantry position display."""
    x = 0
    y = grid_height_mm
    positionChanged = pyqtSignal(int, int)

    def __init__(self, parent=None):
        """Initialize grid view widget.
        
        Args:
            parent: Parent widget (optional).
        
        Return:
            None
        """
        super().__init__(parent)
        self.init()

    def init(self):
        """Initialize grid dimensions and styling.
        
        Args:
            None
        
        Return:
            None
        """
        self.setFixedSize(int(grid_width_mm), int(grid_height_mm))
        self.setStyleSheet("border: 2px solid white;")

    def paintEvent(self, event):
        """Paint grid with lines and position indicator dot.
        
        Args:
            event: Paint event.
        
        Return:
            None
        """
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

    def mousePressEvent(self, event):
        """Handle mouse clicks on grid to move gantry.
        
        Args:
            event: Mouse press event.
        
        Return:
            None
        """
        x = event.pos().x()
        y = event.pos().y()
        self.positionChanged.emit(x, y)
        self.update_dot(x, y)

    def update_dot(self, x, y):
        """Update position indicator dot.
        
        Args:
            x (int): X pixel coordinate.
            y (int): Y pixel coordinate.
        
        Return:
            None
        """
        self.x = x
        self.y = y
        self.update()
        
        self.painter.end()

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
    qss_path = os.path.join(os.path.dirname(__file__), "cnchess_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: QSS theme file not found at {qss_path}")
    settings_view = SettingsView()
    settings_view.show()
    sys.exit(app.exec())