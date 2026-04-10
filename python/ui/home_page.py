"""File for the home page of the application, which is the first page that the user sees when they open the app. 
It contains buttons to choose difficulty, start a new game, and view settings """

import os
import sys
import chess

from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QVBoxLayout, QHBoxLayout, QButtonGroup, QToolButton, QSizePolicy
from PyQt6.QtGui import QIcon, QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import QObject, QSize, Qt, pyqtSignal, QTimer

class HomeView(QWidget):
    """Home page view for difficulty selection and game initialization."""

    def __init__(self, chess_model):
        """Initialize home page view with chess model instance.
        
        Args:
            chess_model: Chess game model instance.
        
        Return:
            None
        """
        super().__init__()
        self.chess_model = chess_model
        self.home_page_controller = HomePageController(chess_model)
        self._difficulty_buttons: list[QToolButton] = []
        self._difficulty_icon_paths: dict[str, str] = {}
        self._difficulty_trimmed_images: dict[str, QImage] = {}
        self._difficulty_icon_cache: dict[tuple[str, int, bool], QIcon] = {}
        self._difficulty_last_side: int | None = None
        self._difficulty_last_checked: dict[str, bool] = {}

        self._difficulty_update_pending = False
        self._difficulty_update_timer = QTimer(self)
        self._difficulty_update_timer.setSingleShot(True)
        self._difficulty_update_timer.timeout.connect(self._update_difficulty_buttons)
        self.init_ui()
    
    def init_ui(self):
        """Initialize home page UI layout with logo, difficulty, and color buttons.
        
        Args:
            None
        
        Return:
            None
        """
        logo_label = QLabel(self)
        logo_path = os.path.join(os.path.dirname(__file__), "assets/CNChess_logo.png")
        trimmed_logo = self._get_trimmed_image(logo_path)
        if trimmed_logo is not None:
            logo_pixmap = QPixmap.fromImage(trimmed_logo)
        else:
            logo_pixmap = QPixmap(logo_path)
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(
                800,
                400,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Prevent the logo label from expanding vertically when the window grows.
            logo_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            logo_label.setMinimumHeight(logo_pixmap.height())
            logo_label.setMaximumHeight(logo_pixmap.height())

        level_layout = self.build_level_buttons()
        time_layout = self.build_time_control_buttons()
        color_layout = self.build_color_buttons()
        menu_layout = self.build_menu_buttons()

        hbox_layout = QHBoxLayout()
        hbox_layout.addStretch(20)
        hbox_layout.addLayout(color_layout)
        hbox_layout.addSpacing(50)
        hbox_layout.addLayout(menu_layout)
        hbox_layout.addStretch(20)

        main_layout = QVBoxLayout()
        main_layout.addStretch(1)
        main_layout.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        main_layout.addSpacing(75)
        main_layout.addLayout(level_layout)
        main_layout.addSpacing(50)
        main_layout.addLayout(time_layout)
        main_layout.addSpacing(75)
        main_layout.addLayout(hbox_layout)
        # Ensure extra vertical space goes to the bottom when the window is large.
        main_layout.addStretch(1)
        self.setLayout(main_layout)

        self._update_difficulty_buttons()

    def _get_trimmed_image(self, image_path: str) -> QImage | None:
        """Get image with transparent areas trimmed.
        
        Args:
            image_path (str): Path to image file.
        
        Return:
            QImage: Trimmed image or None if image not found.
        """
        cached = self._difficulty_trimmed_images.get(image_path)
        if cached is not None:
            return cached

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return None

        image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        rect = image.rect()
        left = rect.right()
        right = rect.left()
        top = rect.bottom()
        bottom = rect.top()
        found = False

        alpha_threshold = 10
        for y in range(rect.top(), rect.bottom() + 1):
            for x in range(rect.left(), rect.right() + 1):
                if image.pixelColor(x, y).alpha() > alpha_threshold:
                    found = True
                    if x < left:
                        left = x
                    if x > right:
                        right = x
                    if y < top:
                        top = y
                    if y > bottom:
                        bottom = y

        if found and right >= left and bottom >= top:
            image = image.copy(left, top, (right - left + 1), (bottom - top + 1))

        self._difficulty_trimmed_images[image_path] = image
        return image

    def _make_filled_square_icon(self, image_path: str, target_size: QSize, *, darken: bool = False) -> QIcon:
        """Create filled square icon from image file.
        
        Args:
            image_path (str): Path to image file.
            target_size (QSize): Target size for icon.
            darken (bool): Whether to darken icon (default False).
        
        Return:
            QIcon: Generated icon.
        """
        side = int(target_size.width())
        cache_key = (image_path, side, darken)
        cached_icon = self._difficulty_icon_cache.get(cache_key)
        if cached_icon is not None:
            return cached_icon

        trimmed = self._get_trimmed_image(image_path)
        if trimmed is None:
            return QIcon()

        pixmap = QPixmap.fromImage(trimmed)

        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )

        x = max(0, (scaled.width() - target_size.width()) // 2)
        y = max(0, (scaled.height() - target_size.height()) // 2)
        cropped = scaled.copy(x, y, target_size.width(), target_size.height())

        if darken:
            painter = QPainter(cropped)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceAtop)
            painter.fillRect(cropped.rect(), QColor(0, 0, 0, 110))
            painter.end()

        icon = QIcon(cropped)
        self._difficulty_icon_cache[cache_key] = icon
        return icon

    def _update_difficulty_buttons(self) -> None:
        """Update difficulty button icons based on current window size and selection state.
        
        Args:
            None
        
        Return:
            None
        """
        self._difficulty_update_pending = False
        if not self._difficulty_buttons:
            return

        # Estimate a responsive square size based on current window width.
        # Keep it within a sensible range so it doesn't get huge.
        side = int((self.width() - 200) / 3)
        side = max(90, min(220, side))
        target = QSize(side, side)

        checked_now = {b.objectName(): b.isChecked() for b in self._difficulty_buttons}
        if self._difficulty_last_side == side and self._difficulty_last_checked == checked_now:
            return

        self._difficulty_last_side = side
        self._difficulty_last_checked = checked_now

        for button in self._difficulty_buttons:
            button.setFixedSize(target)
            button.setIconSize(target)
            path = self._difficulty_icon_paths.get(button.objectName())
            if path:
                button.setIcon(self._make_filled_square_icon(path, target, darken=button.isChecked()))


    def resizeEvent(self, event):
        """Handle window resize events and coalesce frequent updates.
        
        Args:
            event: Resize event.
        
        Return:
            None
        """
        super().resizeEvent(event)
        # Coalesce frequent resize events
        if not self._difficulty_update_pending:
            self._difficulty_update_pending = True
        self._difficulty_update_timer.start(40)

    def build_level_buttons(self):
        """Build difficulty level selection buttons (Easy, Medium, Hard).
        
        Args:
            None
        
        Return:
            QHBoxLayout: Layout containing difficulty buttons.
        """
        level_button_size = QSize(175, 175)

        easy_button = QToolButton(self)
        easy_button.setObjectName("difficultyEasy")
        easy_button.setCheckable(True)
        easy_button.setAutoRaise(True)
        easy_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        easy_path = os.path.join(os.path.dirname(__file__), "assets", "easy_icon.png")
        self._difficulty_icon_paths[easy_button.objectName()] = easy_path
        easy_icon = self._make_filled_square_icon(easy_path, level_button_size)
        easy_button.setIcon(easy_icon)
        easy_button.setIconSize(level_button_size)
        easy_button.setFixedSize(level_button_size)
        easy_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        medium_button = QToolButton(self)
        medium_button.setObjectName("difficultyMedium")
        medium_button.setCheckable(True)
        medium_button.setAutoRaise(True)
        medium_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        medium_path = os.path.join(os.path.dirname(__file__), "assets", "intermediate_icon.png")
        self._difficulty_icon_paths[medium_button.objectName()] = medium_path
        medium_icon = self._make_filled_square_icon(medium_path, level_button_size)
        medium_button.setIcon(medium_icon)
        medium_button.setIconSize(level_button_size)
        medium_button.setFixedSize(level_button_size)
        medium_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        hard_button = QToolButton(self)
        hard_button.setObjectName("difficultyHard")
        hard_button.setCheckable(True)
        hard_button.setAutoRaise(True)
        hard_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        hard_path = os.path.join(os.path.dirname(__file__), "assets", "hard_icon.png")
        self._difficulty_icon_paths[hard_button.objectName()] = hard_path
        hard_icon = self._make_filled_square_icon(hard_path, level_button_size)
        hard_button.setIcon(hard_icon)
        hard_button.setIconSize(level_button_size)
        hard_button.setFixedSize(level_button_size)
        hard_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._difficulty_buttons = [easy_button, medium_button, hard_button]

        # Update icons whenever selection changes (checked state)
        easy_button.toggled.connect(lambda _checked: self._update_difficulty_buttons())
        medium_button.toggled.connect(lambda _checked: self._update_difficulty_buttons())
        hard_button.toggled.connect(lambda _checked: self._update_difficulty_buttons())

        easy_button.clicked.connect(self.home_page_controller.easy_button_clicked)
        medium_button.clicked.connect(self.home_page_controller.medium_button_clicked)
        hard_button.clicked.connect(self.home_page_controller.hard_button_clicked)

        level_group = QButtonGroup(self)
        level_group.addButton(easy_button)
        level_group.addButton(medium_button)
        level_group.addButton(hard_button)
        level_group.setExclusive(True)
        easy_button.setChecked(True)

        layout = QHBoxLayout()
        layout.addStretch(50)
        layout.addWidget(easy_button)
        layout.addWidget(medium_button)
        layout.addWidget(hard_button)
        layout.addStretch(50)

        return layout
    
    def build_time_control_buttons(self):
        """Build time control selection buttons (3 min, 5 min, 10 min, No limit).
        
        Args:
            None
        
        Return:
            QHBoxLayout: Layout containing time control buttons.
        """
        time_3_button = QPushButton("3 MIN", self)
        time_3_button.setCheckable(True)
        time_3_button.setObjectName("time_button")
        time_3_button.setMinimumSize(120, 50)
        time_3_button.clicked.connect(self.home_page_controller.time_3_button_clicked)

        time_5_button = QPushButton("5 MIN", self)
        time_5_button.setCheckable(True)
        time_5_button.setObjectName("time_button")
        time_5_button.setMinimumSize(120, 50)
        time_5_button.clicked.connect(self.home_page_controller.time_5_button_clicked)

        time_10_button = QPushButton("10 MIN", self)
        time_10_button.setCheckable(True)
        time_10_button.setObjectName("time_button")
        time_10_button.setMinimumSize(120, 50)
        time_10_button.clicked.connect(self.home_page_controller.time_10_button_clicked)

        time_none_button = QPushButton("NO LIMIT", self)
        time_none_button.setCheckable(True)
        time_none_button.setObjectName("time_button")
        time_none_button.setMinimumSize(120, 50)
        time_none_button.clicked.connect(self.home_page_controller.time_none_button_clicked)

        time_group = QButtonGroup(self)
        time_group.addButton(time_3_button)
        time_group.addButton(time_5_button)
        time_group.addButton(time_10_button)
        time_group.addButton(time_none_button)
        time_group.setExclusive(True)
        time_none_button.setChecked(True)

        layout = QHBoxLayout()
        layout.addStretch(50)
        layout.addWidget(time_3_button)
        layout.addWidget(time_5_button)
        layout.addWidget(time_10_button)
        layout.addWidget(time_none_button)
        layout.addStretch(50)

        return layout
    
    def build_color_buttons(self):
        """Build player color selection buttons (White, Black).
        
        Args:
            None
        
        Return:
            QHBoxLayout: Layout containing color selection buttons.
        """
        color_button_size = QSize(100, 100)
        color_icon_size = color_button_size + QSize(50, 50)

        white_button = QToolButton(self)
        white_button.setObjectName("colorWhite")
        white_button.setCheckable(True)
        white_button.setAutoRaise(True)
        white_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        white_path = os.path.join(os.path.dirname(__file__), "assets", "white_pawn_icon.png")
        white_trimmed = self._get_trimmed_image(white_path)
        if white_trimmed is not None:
            white_pixmap = QPixmap.fromImage(white_trimmed)
        else:
            white_pixmap = QPixmap(white_path)

        white_button.setIcon(QIcon(white_pixmap))
        white_button.setIconSize(color_icon_size)

        black_button = QToolButton(self)
        black_button.setObjectName("colorBlack")
        black_button.setCheckable(True)
        black_button.setAutoRaise(True)
        black_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        black_path = os.path.join(os.path.dirname(__file__), "assets", "black_pawn_icon.png")
        black_trimmed = self._get_trimmed_image(black_path)
        if black_trimmed is not None:
            black_pixmap = QPixmap.fromImage(black_trimmed)
        else:
            black_pixmap = QPixmap(black_path)
        black_button.setIcon(QIcon(black_pixmap))
        black_button.setIconSize(color_icon_size)

        white_button.clicked.connect(self.home_page_controller.white_button_clicked)
        black_button.clicked.connect(self.home_page_controller.black_button_clicked)

        color_group = QButtonGroup(self)
        color_group.addButton(white_button)
        color_group.addButton(black_button)
        color_group.setExclusive(True)
        white_button.setChecked(True)

        layout = QHBoxLayout()
        layout.addWidget(white_button)
        layout.addWidget(black_button)

        return layout
    
    def build_menu_buttons(self):
        """Build menu buttons (Start Game, Settings).
        
        Args:
            None
        
        Return:
            QVBoxLayout: Layout containing menu buttons.
        """
        start_button = QPushButton("START GAME", self)
        start_button.clicked.connect(self.home_page_controller.start_game)
        start_button.setObjectName("menu_button")
        start_button.setMinimumSize(200, 60)

        settings_button = QPushButton("SETTINGS", self)
        settings_button.clicked.connect(self.home_page_controller.settings_button_clicked)
        settings_button.setObjectName("menu_button")
        settings_button.setMinimumSize(200, 60)

        layout = QVBoxLayout()
        layout.addWidget(start_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(settings_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        return layout

class HomePageController(QObject):
    """Controller for home page user interactions and difficulty/color selection."""
    # Define signals that will be emitted when user wants to navigate
    start_game_signal = pyqtSignal()
    settings_signal = pyqtSignal()

    def __init__(self, chess_model):
        """Initialize home page controller with chess model.
        
        Args:
            chess_model: Chess game model instance.
        
        Return:
            None
        """
        super().__init__()
        self.chess_model = chess_model

    def easy_button_clicked(self):
        """Handle easy difficulty selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_difficulty("easy")

    def medium_button_clicked(self):
        """Handle medium difficulty selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_difficulty("medium")

    def hard_button_clicked(self):
        """Handle hard difficulty selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_difficulty("hard")    

    def time_3_button_clicked(self):
        """Handle 3 minute time control selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_time_control(3)

    def time_5_button_clicked(self):
        """Handle 5 minute time control selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_time_control(5)

    def time_10_button_clicked(self):
        """Handle 10 minute time control selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_time_control(10)

    def time_none_button_clicked(self):
        """Handle no time limit selection.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_time_control(0)

    def white_button_clicked(self):
        """Handle white color selection for player.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_player_color(chess.WHITE)

    def black_button_clicked(self):
        """Handle black color selection for player.
        
        Args:
            None
        
        Return:
            None
        """
        self.chess_model.set_player_color(chess.BLACK)

    def start_game(self):
        """Emit start game signal to navigate to game page.
        
        Args:
            None
        
        Return:
            None
        """
        # Emit the signal instead of directly calling a method
        self.start_game_signal.emit()    
    
    def settings_button_clicked(self):
        """Emit settings signal to navigate to settings page.
        
        Args:
            None
        
        Return:
            None
        """
        self.settings_signal.emit()

if __name__ == "__main__":

    controller = HomePageController(None)

    app = QApplication(sys.argv)
    qss_path = os.path.join(os.path.dirname(__file__), "cnchess_theme.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: QSS theme file not found at {qss_path}")
    home_view = HomeView(None)
    home_view.show()
    sys.exit(app.exec())