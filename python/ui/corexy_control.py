from typing import Optional
from Control import Position, Command
from Communication import Communication
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGraphicsView,
    QGraphicsScene,
    QDoubleSpinBox,
    QLabel,
    QGridLayout,
)
from PyQt6.QtCore import pyqtSignal, pyqtSlot, QObject, QThread, Qt
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter


class CanvasView(QGraphicsView):
    """Clickable graphics view that reports scene coordinates in mm.

    The widget uses an internal scale: 1 scene unit == 1 millimeter.
    """

    clicked = pyqtSignal(float, float)

    def mousePressEvent(self, event):
        pos = self.mapToScene(event.position().toPoint())
        self.clicked.emit(pos.x(), pos.y())
        super().mousePressEvent(event)


class CoreXYControl(QWidget):
    """Main widget exposing controls and a visual scene.

    Signals:
        moveRequested(x: float, y: float)
        jogRequested(dx: float, dy: float)
        homeRequested()
        stopRequested()
    """

    moveRequested = pyqtSignal(float, float)
    jogRequested = pyqtSignal(float, float)
    homeRequested = pyqtSignal()
    stopRequested = pyqtSignal()

    def __init__(self, parent=None, width_mm: float = 400.0, height_mm: float = 300.0):
        super().__init__(parent)

        self.width_mm = width_mm
        self.height_mm = height_mm

        self.scene = QGraphicsScene(0, 0, self.width_mm, self.height_mm)
        self.view = CanvasView(self.scene)
        
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setFixedSize(int(self.width_mm) + 2, int(self.height_mm) + 2)

        # Draw a simple grid
        pen = QPen(QColor(200, 200, 200))
        for x in range(0, int(self.width_mm) + 1, 10):
            self.scene.addLine(x, 0, x, self.height_mm, pen)
        for y in range(0, int(self.height_mm) + 1, 10):
            self.scene.addLine(0, y, self.width_mm, y, pen)

        # Position marker
        self.marker = self.scene.addEllipse(-3, -3, 6, 6, QPen(Qt.GlobalColor.red), QBrush(Qt.GlobalColor.red))
        self.marker.setPos(0, 0)

        # Controls
        self.x_spin = QDoubleSpinBox(); self.x_spin.setRange(0, self.width_mm); self.x_spin.setSuffix(' mm')
        self.y_spin = QDoubleSpinBox(); self.y_spin.setRange(0, self.height_mm); self.y_spin.setSuffix(' mm')
        self.go_button = QPushButton('Go')

        # Jog buttons
        self.jog_up = QPushButton('▲')
        self.jog_down = QPushButton('▼')
        self.jog_left = QPushButton('◄')
        self.jog_right = QPushButton('►')
        self.jog_step = QDoubleSpinBox(); self.jog_step.setRange(0.1, 100); self.jog_step.setValue(5); self.jog_step.setSuffix(' mm')

        # Home/Stop
        self.home_button = QPushButton('Home')
        self.stop_button = QPushButton('Stop')

        # Status
        self.status_label = QLabel('Idle')

        # Layout
        right = QVBoxLayout()
        grid = QGridLayout()
        grid.addWidget(QLabel('X:'), 0, 0); grid.addWidget(self.x_spin, 0, 1)
        grid.addWidget(QLabel('Y:'), 1, 0); grid.addWidget(self.y_spin, 1, 1)
        grid.addWidget(self.go_button, 2, 0, 1, 2)

        jog_layout = QGridLayout()
        jog_layout.addWidget(self.jog_up, 0, 1)
        jog_layout.addWidget(self.jog_left, 1, 0); jog_layout.addWidget(self.jog_step, 1, 1); jog_layout.addWidget(self.jog_right, 1, 2)
        jog_layout.addWidget(self.jog_down, 2, 1)

        right.addLayout(grid)
        right.addLayout(jog_layout)
        right.addWidget(self.home_button)
        right.addWidget(self.stop_button)
        right.addWidget(self.status_label)
        right.addStretch()

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.view)
        main_layout.addLayout(right)

        # Connections
        self.go_button.clicked.connect(self._on_go_clicked)
        self.jog_up.clicked.connect(lambda: self._on_jog(0, self.jog_step.value()))
        self.jog_down.clicked.connect(lambda: self._on_jog(0, -self.jog_step.value()))
        self.jog_left.clicked.connect(lambda: self._on_jog(-self.jog_step.value(), 0))
        self.jog_right.clicked.connect(lambda: self._on_jog(self.jog_step.value(), 0))
        self.home_button.clicked.connect(lambda: self.homeRequested.emit())
        self.stop_button.clicked.connect(lambda: self.stopRequested.emit())
        self.view.clicked.connect(self._on_canvas_clicked)

    def _on_go_clicked(self):
        x = float(self.x_spin.value())
        y = float(self.y_spin.value())
        if 0 <= x <= self.width_mm and 0 <= y <= self.height_mm:
            self.moveRequested.emit(x, y)
            self.set_status(f'Requested move to {x:.1f}, {y:.1f} mm')
        else:
            self.set_status('Target out of bounds')

    def _on_jog(self, dx: float, dy: float):
        self.jogRequested.emit(dx, dy)
        self.set_status(f'Jog {dx:.1f}, {dy:.1f} mm')

    def _on_canvas_clicked(self, x: float, y: float):
        # snap into bounds
        x = max(0.0, min(self.width_mm, x))
        y = max(0.0, min(self.height_mm, y))
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
        self.moveRequested.emit(x, y)
        self.set_status(f'Canvas click -> {x:.1f}, {y:.1f} mm')

    @pyqtSlot(float, float)
    def update_position(self, x: float, y: float):
        self.marker.setPos(x, y)
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)

    @pyqtSlot(str)
    def set_status(self, text: str):
        self.status_label.setText(text)


class CoreXYWorker(QObject):
    """Worker skeleton to run hardware I/O in another thread.

    Pass an object implementing the minimal communication interface. The
    worker attempts to call intuitive methods if available; adapt as
    needed to your `Communication` class.
    """

    positionUpdated = pyqtSignal(float, float)
    status = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, communication: Communication):
        super().__init__()
        self.comm = communication
        self._running = True
        self._last_x = 0.0
        self._last_y = 0.0

    @pyqtSlot(float, float)
    def move_to(self, x: float, y: float):
        try:
            self.status.emit(f'Moving to {x:.1f}, {y:.1f} mm')

            pos = Position(x,y)
    
            hasMove = self.comm.send_position(pos)
    
            self._last_x = x; self._last_y = y
            self.positionUpdated.emit(x, y)

            if hasMove:
                self.status.emit('Move complete')
            else:
                self.status.emit('Move failed')
            return
        
        except Exception as e:
            self.error.emit(str(e))

    @pyqtSlot(float, float)
    def jog(self, dx: float, dy: float):
        try:
            self.status.emit(f'Jog {dx:.1f}, {dy:.1f} mm')
            
            self.comm.jog(dx, dy)
            
            self._last_x += dx; self._last_y += dy
            self.positionUpdated.emit(self._last_x, self._last_y)
            self.status.emit('Jog complete')
            
        except Exception as e:
            self.error.emit(str(e))

    @pyqtSlot()
    def home(self):
        try:
            self.status.emit('Homing')
            self.comm.goHome()
            self._last_x = 0.0; self._last_y = 0.0
            self.positionUpdated.emit(0.0, 0.0)
            self.status.emit('Homed')
        except Exception as e:
            self.error.emit(str(e))

    @pyqtSlot()
    def stop(self):
        try:
            self.status.emit('Stop requested')
            self.comm.stop()
            self.status.emit('Stopped')
        except Exception as e:
            self.error.emit(str(e))
