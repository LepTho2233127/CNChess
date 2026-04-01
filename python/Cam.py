import cv2
import numpy as np
import json
import ctypes
import chess
import time

"""Camera pipeline for board calibration, perspective warp, piece detection, and move detection."""

class ImageCalibration:
    """Handle manual board-corner calibration from an image source."""
    
    def __init__(self, image_path: str, scale: float = 1.0):
        """Initialize calibration with image path and scale factor.
        
        Args:
            image_path (str): Path to calibration image file.
            scale (float): Scale factor for image display (default 1.0).
        
        Return:
            None
        """
        self.image_path = image_path
        self.scale = scale
        self.points = []
        self.calibration_file = 'calibration_points.json'
        
    def mouse_click(self, event, x, y, flags, param):
        """Store clicked board-corner points.

        Args:
            event: OpenCV mouse event code.
            x: Mouse x-coordinate in displayed image space.
            y: Mouse y-coordinate in displayed image space.
            flags: OpenCV mouse flags (unused).
            param: Scale factor used to map display coordinates to original image.

        Return:
            None
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < 4:
                orig_x = int(x / param)
                orig_y = int(y / param)
                self.points.append((orig_x, orig_y))
                print(f"[INFO] Point {len(self.points)}: {orig_x}, {orig_y}")
            else:
                print("[INFO] Already 4 points. Press 'r' to reset.")
    
    @staticmethod
    def center_window(window_name: str, width: int, height: int):
        """Center an OpenCV window on screen.

        Args:
            window_name (str): OpenCV window name.
            width (int): Window width in pixels.
            height (int): Window height in pixels.

        Return:
            None
        """
        try:
            import subprocess
            output = subprocess.check_output(['xdpyinfo'], stderr=subprocess.DEVNULL).decode()
            for line in output.split('\n'):
                if 'dimensions:' in line:
                    dims = line.split()[1].split('x')
                    screen_w, screen_h = int(dims[0]), int(dims[1])
                    break
            else:
                screen_w, screen_h = 1920, 1080
        except Exception:
            screen_w, screen_h = 1920, 1080
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        cv2.moveWindow(window_name, x, y)
    
    def calibrate(self, frame: np.ndarray = None):
        """Run interactive 4-point board calibration.

        Args:
            frame (np.ndarray, optional): Optional camera frame to calibrate from.

        Return:
            None
        """
        if frame is not None:
            # Use captured frame as calibration source.
            image = cv2.resize(frame, None, fx=self.scale, fy=self.scale)
            print("[INFO] Photo captured from camera")
        else:
            # Load calibration source from disk.
            orig_image = cv2.imread(self.image_path)
            image = cv2.resize(orig_image, None, fx=self.scale, fy=self.scale)
            print("[INFO] Image loaded from file")
        
        cv2.namedWindow("Calibration Plateau", cv2.WINDOW_NORMAL)
        
        h, w = image.shape[:2]
        self.center_window("Calibration Plateau", w, h)
        
        cv2.setMouseCallback("Calibration Plateau", self.mouse_click, param=self.scale)
        
        print("[INFO] Click on the 4 corners of the board (top-left, top-right, bottom-left, bottom-right)")
        print("[INFO] Press 'R' to reset or wait for the 4 points to be detected")
        
        first_display = True
        
        while True:
            vis = image.copy()
            
            # Draw selected corner points and labels.
            for idx, (ox, oy) in enumerate(self.points):
                x = int(ox * self.scale)
                y = int(oy * self.scale)
                cv2.circle(vis, (x, y), 6, (0, 0, 255), -1)
                cv2.circle(vis, (x, y), 8, (255, 255, 255), 2)  # White border
                cv2.putText(vis, str(idx+1), (x+8, y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Calibration Plateau", vis)
            cv2.resizeWindow("Calibration Plateau", vis.shape[1], vis.shape[0])
            if first_display:
                print("[INFO] Photo displayed - waiting for clicks on corners")
                first_display = False
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('r'):
                print("[INFO] Resetting points")
                self.points = []
            elif key == ord('q'):
                print("[INFO] Calibration cancelled")
                cv2.destroyAllWindows()
                return
            
            if len(self.points) == 4:
                print("[INFO] 4 points detected ✓")
                break
        
        cv2.destroyAllWindows()
        print("[INFO] Calibration complétée")
        self.save_calibration()
    
    def save_calibration(self):
        """Save selected board-corner points to the calibration JSON file.

        Return:
            None
        """
        calibration_points = {
            "top_left": self.points[0],
            "top_right": self.points[1],
            "bottom_right": self.points[2],
            "bottom_left": self.points[3]
        }
        
        with open(self.calibration_file, 'w') as f:
            json.dump(calibration_points, f, indent=4)
        
        print("[INFO] Calibration saved to calibration_points.json")
    
    def load_calibration(self) -> dict:
        """Load board-corner calibration points from JSON.

        Return:
            dict: Calibration points dictionary.
        """
        with open(self.calibration_file, 'r') as f:
            return json.load(f)


class ChessBoardTransform:
    """Handle perspective transforms between camera view and top-down board view."""

    def __init__(self, calibration_points: dict, board_size: int = 1200):
        """Initialize transform with calibration points and board size.
        
        Args:
            calibration_points (dict): Dictionary with corner points (top_left, top_right, bottom_right, bottom_left).
            board_size (int): Target board size in pixels (default 1200).
        
        Return:
            None
        """
        self.top_left = tuple(calibration_points["top_left"])
        self.top_right = tuple(calibration_points["top_right"])
        self.bottom_right = tuple(calibration_points["bottom_right"])
        self.bottom_left = tuple(calibration_points["bottom_left"])
        
        self.board_size = board_size
        self.threshold = 0
        self.M = None
        self.M_inv = None
        
    def compute_transform_matrix(self):
        """Compute the perspective transform matrix.

        Return:
            None
        """
        extreme_points_list = np.float32([
            self.top_left, self.top_right, 
            self.bottom_left, self.bottom_right
        ])
        
        dst_pts = np.float32([
            [self.threshold, self.threshold], 
            [self.board_size + self.threshold, self.threshold], 
            [self.threshold, self.board_size + self.threshold], 
            [self.board_size + self.threshold, self.board_size + self.threshold]
        ])
        
        self.M = cv2.getPerspectiveTransform(extreme_points_list, dst_pts)
        #self.M_inv = cv2.invert(self.M)[1]
    
    def apply_transform(self, image: np.ndarray) -> np.ndarray:
        """Apply perspective transform and return normalized board image.

        Args:
            image (np.ndarray): Input image in camera perspective.

        Return:
            np.ndarray: Warped board image.
        """
        if self.M is None:
            self.compute_transform_matrix()
        
        warped = cv2.warpPerspective(
            image, self.M, 
            (self.board_size + 2 * self.threshold, 
             self.board_size + 2 * self.threshold)
        )
        return warped
    
    def inverse_transform(self, points: np.ndarray) -> np.ndarray:
        """Project points from warped space to source image space.

        Args:
            points (np.ndarray): Points in warped board coordinates.

        Return:
            np.ndarray: Points projected back to source image coordinates.
        """
        if self.M_inv is None:
            self.compute_transform_matrix()
        
        return cv2.perspectiveTransform(points, self.M_inv)


class ColorMask:
    """Create color masks used for piece-marker segmentation."""
    # HSV ranges for marker colors.
    # Yellow: H around 20-40.
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])

    # Green: H around 40-90.
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])

    @staticmethod
    def create_color_mask(image_rgb):
        """Build a binary mask for yellow and green markers.

        Args:
            image_rgb: RGB image to segment.

        Return:
            tuple: (masked RGB image, combined binary mask).
        """
        # HSV makes color thresholding more robust than RGB.
        hsv_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        
        # Build separate masks for each target color.
        mask_yellow = cv2.inRange(hsv_image, ColorMask.lower_yellow, ColorMask.upper_yellow)
        mask_green = cv2.inRange(hsv_image, ColorMask.lower_green, ColorMask.upper_green)

        # Merge color masks into one foreground mask.
        combined_mask = cv2.bitwise_or(mask_yellow, mask_green)

        # Remove small holes/noise.
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Keep only masked marker pixels in the output image.
        masked_image = cv2.bitwise_and(image_rgb, image_rgb, mask=combined_mask)
        
        return masked_image, combined_mask
    
class ChessBoardSquares:
    """Provide utilities to index and draw board squares on warped images."""

    ROWS, COLS = 8, 8
    def __init__(self, board_size: int):
        """Initialize square geometry from board size.

        Args:
            board_size (int): Board width/height in pixels.

        Return:
            None
        """
        self.board_size = board_size
        self.square_width = board_size // self.COLS
        self.square_height = board_size // self.ROWS

    def get_square_region(self, warped_image: np.ndarray, square_index: int, 
                         padding_ratio: float = 0.2) -> np.ndarray:
        """Extract a padded region of one board square.

        Args:
            warped_image (np.ndarray): Warped board image.
            square_index (int): Square index from 0 to 63.
            padding_ratio (float): Relative padding removed from each side.

        Return:
            np.ndarray: Cropped square image.
        """
        row = self.COLS - 1 - (square_index) // self.COLS
        col = (square_index) % self.COLS
        
        full_region = warped_image[
            row * self.square_height : (row + 1) * self.square_height,
            col * self.square_width : (col + 1) * self.square_width
        ]
        
        pad_height = int(self.square_height * padding_ratio)
        pad_width = int(self.square_width * padding_ratio)
        
        square_region = full_region[
            pad_height : self.square_height - pad_height,
            pad_width : self.square_width - pad_width
        ]
        
        return square_region
    
    def draw_grid(self, image: np.ndarray, color: tuple = (0, 255, 0), 
                  thickness: int = 4) -> np.ndarray:
        """Draw an 8x8 board grid on an image.

        Args:
            image (np.ndarray): Input image.
            color (tuple): Grid line color in BGR.
            thickness (int): Grid line thickness in pixels.

        Return:
            np.ndarray: Image with grid overlay.
        """
        vis = image.copy()
        
        for i in range(self.ROWS):
            for j in range(self.COLS):
                top_left = (j * self.square_width, i * self.square_height)
                bottom_right = ((j + 1) * self.square_width, (i + 1) * self.square_height)
                cv2.rectangle(vis, top_left, bottom_right, color, thickness)
        
        return vis
    
    def get_all_squares_warped(self) -> list:
        """Return coordinates for all warped squares in board order.

        Return:
            list: List of square center and corner coordinates.
        """
        squares_data = []
        
        for i in range(self.ROWS - 1, -1, -1):
            for j in range(self.COLS):
                top_left = (j * self.square_width, i * self.square_height)
                top_right = ((j + 1) * self.square_width, i * self.square_height)
                bottom_left = (j * self.square_width, (i + 1) * self.square_height)
                bottom_right = ((j + 1) * self.square_width, (i + 1) * self.square_height)
                
                x_center = (top_left[0] + bottom_right[0]) // 2
                y_center = (top_left[1] + bottom_right[1]) // 2
                
                squares_data.append([
                    (x_center, y_center),
                    bottom_right,
                    top_right,
                    top_left,
                    bottom_left
                ])
        
        return squares_data


# ============================================================================
# CLASS: PieceDetection
# ============================================================================
class PieceDetection:
    """Detect piece occupancy and marker color from masked square regions."""
    
    def __init__(self, warped_image: np.ndarray, board_squares: ChessBoardSquares):
        """Initialize detector with a masked warped image and board geometry.

        Args:
            warped_image (np.ndarray): Masked warped board image.
            board_squares (ChessBoardSquares): Square helper utilities.

        Return:
            None
        """
        self.warped_image = warped_image
        self.board_squares = board_squares
    
    # def calculate_baseline_variance(self, empty_indices: list = None) -> float:
    #     """Calculates baseline variance of an empty square (kept for API compatibility)"""
    #     self.baseline_variance = 1.0  # Not used in pixel-count detection
    #     return self.baseline_variance
    
    def detect_piece_in_square(self, square_index: int,
                              threshold_multiplier: float = 1.0,
                              min_pixel_ratio: float = 0.02) -> str:
        """Detect whether a square is occupied.

        Args:
            square_index (int): Square index from 0 to 63.
            threshold_multiplier (float): Reserved parameter for compatibility.
            min_pixel_ratio (float): Minimum non-black pixel ratio for occupancy.

        Return:
            str: 'empty' if no piece is detected, else detected color label.
        """
        square_region = self.board_squares.get_square_region(self.warped_image, square_index, padding_ratio=0.33)
        
        # The color mask already removed most of the board background.
        gray = cv2.cvtColor(square_region, cv2.COLOR_RGB2GRAY) if len(square_region.shape) == 3 else square_region
        non_black_count = np.count_nonzero(gray > 10)
        total_pixels = gray.shape[0] * gray.shape[1]
        
        if total_pixels == 0:
            return 'empty'
        
        ratio = non_black_count / total_pixels
        
        if ratio > min_pixel_ratio:
            return self._get_piece_color(square_index, min_pixel_ratio)
        else:
            return 'empty'
    
    def _get_piece_color(self, square_index: int, min_pixel_ratio: float = 0.02) -> str:
        """Classify marker color in one square.

        Args:
            square_index (int): Square index from 0 to 63.
            min_pixel_ratio (float): Minimum occupancy ratio to attempt color classification.

        Return:
            str: One of 'yellow', 'green', 'unknown', or 'empty'.
        """
        square_region = self.board_squares.get_square_region(self.warped_image, square_index, padding_ratio=0.33)

        if square_region.shape[2] != 3:
            return 'empty'
        
        # Re-check occupancy before attempting color classification.
        gray = cv2.cvtColor(square_region, cv2.COLOR_RGB2GRAY) if len(square_region.shape) == 3 else square_region
        non_black_count = np.count_nonzero(gray > 10)
        total_pixels = gray.shape[0] * gray.shape[1]

        if total_pixels == 0:
            return 'empty'
        
        ratio = non_black_count / total_pixels


        if ratio < min_pixel_ratio:
            return 'empty'
        
        hsv_region = cv2.cvtColor(square_region.astype(np.uint8), cv2.COLOR_RGB2HSV)
        hsv_colored = hsv_region[gray > 10]  # Evaluate color only on foreground pixels.
        
        h_mean = np.mean(hsv_colored[:, 0])
        s_mean = np.mean(hsv_colored[:, 1])
        v_mean = np.mean(hsv_colored[:, 2])
        
        if s_mean < 30 or v_mean < 30:
            return 'empty'
        
        if 15 < h_mean < 40:
            return 'yellow'
        elif 40 <= h_mean < 100:
            return 'green'
        else:
            return 'unknown'
    
    def detect_all_pieces(self, ratio: float = 0.02) -> tuple[list, list]:
        """Detect occupancy and color for all 64 squares.

        Args:
            ratio (float): Minimum occupancy ratio used for classification.

        Return:
            tuple[list, list]: (piece_place, piece_color) arrays.
        """
        piece_place = [0] * 64
        piece_color = ['empty'] * 64
        
        for i in range(64):
            color = self._get_piece_color(i, ratio)
            
            if color != 'empty':
                piece_place[i] = 1
                piece_color[i] = color
            else:
                piece_place[i] = 0
                piece_color[i] = 'empty'

        return piece_place, piece_color

# ============================================================================
# CLASS: MoveDetection
# ============================================================================
class MoveDetection:
    """Infer moves by comparing camera-detected state and chess engine board state."""
    
    def __init__(self, chess_game):
        """Initialize move detection with a chess game model.

        Args:
            chess_game: Chess game object exposing get_board().

        Return:
            None
        """
        self.chess_game = chess_game
        
    def init_from_board(self) -> tuple[list, list]:
        """Build occupancy and color arrays from the chess engine board.

        Return:
            tuple[list, list]: (old_piece_place, old_piece_color) arrays.
        """
        board = self.chess_game.get_board()
        old_piece_place = [0] * 64
        old_piece_color = ['empty'] * 64
        
        # Convert engine board content into occupancy/color arrays.
        for square_index in range(64):
            piece = board.piece_at(square_index)
            
            if piece is None:
                # Empty square.
                old_piece_place[square_index] = 0
                old_piece_color[square_index] = 'empty'
            else:
                # Occupied square.
                old_piece_place[square_index] = 1
                # Map engine side to camera marker colors.
                old_piece_color[square_index] = 'yellow' if piece.color == chess.WHITE else 'green'

        return old_piece_place, old_piece_color

    def detect_castling(self, old_piece_place: list, old_piece_color: list,
                        new_piece_place: list, new_piece_color: list) -> dict:
        """Detect castling patterns from old and new board states.

        Args:
            old_piece_place (list): Previous occupancy array.
            old_piece_color (list): Previous color array.
            new_piece_place (list): Current occupancy array.
            new_piece_color (list): Current color array.

        Return:
            dict: Move dictionary when castling is detected, else None.
        """
        if (old_piece_place[0] and old_piece_place[4] and new_piece_place[2] and new_piece_place[3] 
            and not old_piece_place[1] and not old_piece_place[2] and not old_piece_place[3]):
            if old_piece_color[0] == old_piece_color[4] == new_piece_color[2] == new_piece_color[3]:
                return {'move_start': 1, 'move_end': 3, 'uci': 'e1c1'}  # Queenside castling
            
        if (old_piece_place[7] and old_piece_place[4] and new_piece_place[5] and new_piece_place[6] 
            and not old_piece_place[5] and not old_piece_place[6]):
            if old_piece_color[7] == old_piece_color[4] == new_piece_color[5] == new_piece_color[6]:
                return {'move_start': 8, 'move_end': 6, 'uci': 'e1g1'}  # Kingside castling
            
        if (old_piece_place[56] and old_piece_place[60] and new_piece_place[58] and new_piece_place[59] 
            and not old_piece_place[57] and not old_piece_place[58] and not old_piece_place[59]):
            if old_piece_color[56] == old_piece_color[60] == new_piece_color[58] == new_piece_color[59]:
                return {'move_start': 57, 'move_end': 59, 'uci': 'e8c8'}  # Queenside castling
            
        if (old_piece_place[63] and old_piece_place[60] and new_piece_place[61] and new_piece_place[62] 
            and not old_piece_place[61] and not old_piece_place[62]):
            if old_piece_color[63] == old_piece_color[60] == new_piece_color[61] == new_piece_color[62]:
                return {'move_start': 64, 'move_end': 62, 'uci': 'e8g8'}  # Kingside castling
    
    def detect_move(self, new_piece_place: list, new_piece_color: list) -> dict:
        """Detect a move from camera state relative to chess engine state.

        Args:
            new_piece_place (list): Current occupancy array from camera.
            new_piece_color (list): Current color array from camera.

        Return:
            dict: Move information with start, end, and UCI fields.
        """
        analyses = [0] * 64
        old_piece_place, old_piece_color = self.init_from_board()
        move_start = 0
        move_end = 0
        
        # Castling has a distinct multi-square pattern and is handled first.
        castling_move = self.detect_castling(old_piece_place, old_piece_color, new_piece_place, new_piece_color)
        if castling_move is not None:
            return castling_move
        
        # Track candidate departure and arrival squares for regular moves.
        piece_disappearances = []
        piece_appearances = []
        
        for i in range(len(new_piece_place)):
            analyses[i] = new_piece_place[i] + old_piece_place[i]
            
            # Capture-like pattern: occupied before and after, but color changed.
            if analyses[i] == 2 and old_piece_color[i] != new_piece_color[i]:
                piece_appearances.append(i+1)
            # Piece appeared (0 -> 1).
            elif analyses[i] == 1 and new_piece_place[i] == 1:
                piece_appearances.append(i+1)
            # Piece disappeared (1 -> 0).
            elif analyses[i] == 1 and new_piece_place[i] == 0:
                piece_disappearances.append(i+1)
        
        # Use first detected candidates as move endpoints.
        if piece_disappearances:
            move_start = piece_disappearances[0]
        if piece_appearances:
            move_end = piece_appearances[0]
        
        uci_move = self.get_uci_move(move_start, move_end)
        
        return {
            'move_start': move_start,
            'move_end': move_end,
            'uci': uci_move
        }
    
    def get_uci_move(self, move_start: int, move_end: int) -> str:
        """Convert 1-based square indices to UCI notation.

        Args:
            move_start (int): Start square index in [1, 64].
            move_end (int): End square index in [1, 64].

        Return:
            str: UCI move string, or 'unknown' when indices are invalid.
        """
        if move_start == 0 or move_end == 0:
            return 'unknown'
        
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['1', '2', '3', '4', '5', '6', '7', '8']
        start_file = files[(move_start - 1) % 8]
        start_rank = ranks[(move_start - 1) // 8]
        end_file = files[(move_end - 1) % 8]
        end_rank = ranks[(move_end - 1) // 8]

        print(f"Detected move: {start_file}{start_rank}{end_file}{end_rank}")

        return f"{start_file}{start_rank}{end_file}{end_rank}"
        


class Cam:
    """Orchestrate calibration, camera capture, piece detection, and move extraction."""
    
    def __init__(self, chess_game, board_size: int = 1200, camera_id: int = 0, scale: float = 1.0):
        """Initialize camera instance with game model and configuration.
        
        Args:
            chess_game: Chess game model instance.
            board_size (int): Target board size in pixels (default 1200).
            camera_id (int): Camera device ID (default 0).
            scale (float): Scale factor for image processing (default 1.0).
        
        Return:
            None
        """
        self.chess_game = chess_game
        self.board_size = board_size
        self.scale = scale
        self.camera_id = camera_id
        self.image_path = None
        
        self.calibration = None
        self.squares = ChessBoardSquares(board_size)
        self.move_detector = MoveDetection(chess_game)
        self.transform = None
        self.cap = None
    
    def initialize_camera(self, calibrate: bool = False):
        """Initialize camera settings and perspective transform.

        Args:
            calibrate (bool): Whether to run calibration before loading transform.

        Return:
            bool: True when initialization succeeds, False otherwise.
        """
        self.cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            print("[ERROR] Unable to open the camera")
            return False
        
        # Favor stable, low-latency capture settings.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
        
        # Log effective settings reported by the driver.
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("[INFO] Camera initialized successfully")
        # print(f"[INFO] Requested resolution: 1920x1080")
        print(f"[INFO] Actual resolution: {actual_width}x{actual_height}")
        
        # Warm up the camera so exposure/white balance can settle.
        print("[INFO] Stabilizing camera (2 seconds)...")
        for _ in range(10):
            self.cap.read()
      
        
        if calibrate:
            self.calibrate_from_camera()
        
        calibration_points = self.load_calibration()
        self.transform = ChessBoardTransform(calibration_points, self.board_size)
        self.transform.compute_transform_matrix()
        
        return True
    
    def recalibrate_from_UI(self):
        """Trigger calibration flow and rebuild transform from updated points.

        Return:
            None
        """

        self.calibrate_from_camera()
        
        calibration_points = self.load_calibration()
        self.transform = ChessBoardTransform(calibration_points, self.board_size)
        self.transform.compute_transform_matrix()

    def calibrate_from_camera(self):
        """Capture one frame and run interactive calibration.

        Return:
            None
        """
        print("[INFO] Starting calibration from camera...")
        print("[INFO] Capturing a photo...")
        
        frame = self.capture_frame()
        if frame is None:
            print("[ERROR] Unable to capture from camera")
            return
        
        print("[INFO] Photo captured ✓")
        
        # Build calibration helper and feed it the captured frame.
        self.calibration = ImageCalibration("camera", scale=self.scale)
        self.calibration.calibrate(frame=frame)

    def load_calibration(self) -> dict:
        """Load calibration points from disk.

        Return:
            dict: Calibration points dictionary.
        """
        if self.calibration is None:
            self.calibration = ImageCalibration("camera")
        
        return self.calibration.load_calibration()
    
    def capture_frame(self, show: bool = False) -> np.ndarray:
        """Capture the most recent camera frame.

        Args:
            show (bool): Whether to display the captured frame.

        Return:
            np.ndarray: Captured frame in BGR, or None on failure.
        """
        if self.cap is None or not self.cap.isOpened():
            print("[ERROR] Camera is not initialized")
            return None
        
        # Flush buffered frames to reduce stale-image latency.
        for _ in range(5):
            self.cap.grab()
        
        ret, frame = self.cap.retrieve()
        if not ret:
            print("[ERROR] Unable to read from camera")
            return None
        if show:
            cv2.namedWindow("Raw Frame Captured", cv2.WINDOW_NORMAL)
            cv2.imshow("Raw Frame Captured", frame)
            cv2.resizeWindow("Raw Frame Captured", frame.shape[1], frame.shape[0])
        return frame
    
    def process_frame(self) -> dict:
        """Process live camera frames until a stable board state is detected.

        Return:
            dict: Detection outputs including frame, board state, and move info.
        """
        timout = 5
        start_time = time.time()
        frame_history = []
        max_history = 3

        while True:
            if time.time() - start_time > timout:
                print("[ERROR] Timeout while waiting for stable frames")
                return None

            frame = self.capture_frame()
            if frame is None:
                return None
            
            time.sleep(0.05)  # Small delay between attempts.
            # Match the RGB processing path used by the rest of the pipeline.
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Warp camera view into a normalized top-down board image.
            warped = self.transform.apply_transform(rgb_image)
            
            # Keep only marker colors used for piece detection.
            masked_warped, mask = ColorMask.create_color_mask(warped)
            
            # Detect occupancy and marker color for each square.
            piece_detector = PieceDetection(masked_warped, self.squares)
            piece_place, piece_color = piece_detector.detect_all_pieces()

            current_state = {
                'piece_place': piece_place.copy(),
                'piece_color': piece_color.copy()
            }

            frame_history.append(current_state)
            if len(frame_history) > max_history:
                frame_history.pop(0)
            
            frame_stable = False
            if len(frame_history) == max_history:
                if(frame_history[0]['piece_place'] == frame_history[1]['piece_place'] == frame_history[2]['piece_place'] and
                frame_history[0]['piece_color'] == frame_history[1]['piece_color'] == frame_history[2]['piece_color']):
                    print("[INFO] Stable state detected across 3 frames, proceeding with move detection")
                    frame_stable = True
                    break
                

        # Only compute move when multiple consecutive frames agree.
        if frame_stable:
            move_info = self.move_detector.detect_move(
                piece_place,
                piece_color
            )
        else:
            move_info = {'move_start': 0, 'move_end': 0, 'uci': 'unknown'}
        
        return {
            'original_frame': frame,
            'warped_image': masked_warped,
            'piece_place': piece_place,
            'piece_color': piece_color,
            'move': move_info
        }
    
    def process_image(self, image_path: str = None) -> dict:
        """Process a static image path or fallback to live frame processing.

        Args:
            image_path (str, optional): Input image path. If None, process live camera.

        Return:
            dict: Detection outputs including board state and move info.
        """
        if image_path:
            # Load image from file.
            orig_image = cv2.imread(image_path)
            rgb_image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        else:
            # Defer to live camera path.
            return self.process_frame()
        
        # Warp camera view into normalized board space.
        warped = self.transform.apply_transform(rgb_image)
        
        # Keep only relevant marker colors.
        masked_warped, mask = ColorMask.create_color_mask(warped)
        
        # Detect occupancy and marker color.
        piece_detector = PieceDetection(masked_warped, self.squares)
        piece_place, piece_color = piece_detector.detect_all_pieces()
        
        # Infer move from detected state against current chess model state.
        move_info = self.move_detector.detect_move(
            piece_place,
            piece_color
        )
        
        return {
            'warped_image': masked_warped,
            'piece_place': piece_place,
            'piece_color': piece_color,
            'move': move_info
        }
    
    def release(self):
        """Release camera resources.

        Return:
            None
        """
        if self.cap is not None:
            self.cap.release()
            print("[INFO] Camera released")


# =============================
# Usage example
# =============================
if __name__ == "__main__":
    # Example standalone run.
    import chess, CNChess  # or from your_module import ChessGame
    
    # Create chess model.
    chess_game = CNChess.CNChess()  # Adjust constructor as needed
    
    # Calibrate then analyze a frame.
    cam = Cam(chess_game=chess_game, board_size=1200, camera_id=1)
    cam.initialize_camera(calibrate=True)
    
    # Analyze captured frame.
    result = cam.process_image()
    
    if result:
        print("\n=== RESULTS ===")
        print(f"Pieces detected: {sum(result['piece_place'])}")
        print(f"UCI move: {result['move']['uci']}")
        
        # Show analyzed image with board grid.
        display_image = cv2.cvtColor(result['warped_image'], cv2.COLOR_RGB2BGR)
        display_image_with_grid = cam.squares.draw_grid(display_image, color=(0, 255, 0), thickness=2)
        cv2.namedWindow("Analyzed Chessboard", cv2.WINDOW_NORMAL)
        cv2.imshow("Analyzed Chessboard", display_image_with_grid)
        cv2.resizeWindow("Analyzed Chessboard", display_image_with_grid.shape[1], display_image_with_grid.shape[0])
        print("[INFO] Press any key to close the image")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    result = cam.process_image()
    
    if result:
        print("\n=== RESULTS ===")
        print(f"Pieces detected: {sum(result['piece_place'])}")
        print(f"UCI move: {result['move']['uci']}")
        
        # Show analyzed image with board grid.
        display_image = cv2.cvtColor(result['warped_image'], cv2.COLOR_RGB2BGR)
        display_image_with_grid = cam.squares.draw_grid(display_image, color=(0, 255, 0), thickness=2)
        cv2.namedWindow("Analyzed Chessboard", cv2.WINDOW_NORMAL)
        cv2.imshow("Analyzed Chessboard", display_image_with_grid)
        cv2.resizeWindow("Analyzed Chessboard", display_image_with_grid.shape[1], display_image_with_grid.shape[0])
        print("[INFO] Press any key to close the image")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    

    cam.release()