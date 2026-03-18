import cv2
import numpy as np
import json
import ctypes
import chess

## Extracting Chess Squares with Perspective Transformation (image --> fen format)

class ImageCalibration:
    
    def __init__(self, image_path: str, scale: float = 1.0):
        self.image_path = image_path
        self.scale = scale
        self.points = []
        self.calibration_file = 'calibration_points.json'
        
    def mouse_click(self, event, x, y, flags, param):
        """Callback for mouse clicks"""
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
        """Centers the window on the screen"""
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
        """Launches interactive calibration (from file or camera frame)"""
        if frame is not None:
            # Use the frame passed as parameter
            image = cv2.resize(frame, None, fx=self.scale, fy=self.scale)
            print("[INFO] Photo captured from camera")
        else:
            # Load from file
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
            
            # Draw the points
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
        """Saves calibration points to JSON"""
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
        """Loads calibration points from JSON"""
        with open(self.calibration_file, 'r') as f:
            return json.load(f)


class ChessBoardTransform:
    """Manages perspective transformation of the board"""

    def __init__(self, calibration_points: dict, board_size: int = 1200):
        self.top_left = tuple(calibration_points["top_left"])
        self.top_right = tuple(calibration_points["top_right"])
        self.bottom_right = tuple(calibration_points["bottom_right"])
        self.bottom_left = tuple(calibration_points["bottom_left"])
        
        self.board_size = board_size
        self.threshold = 0
        self.M = None
        self.M_inv = None
        
    def compute_transform_matrix(self):
        """Computes the perspective transformation matrix"""
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
        """Applies perspective transformation"""
        if self.M is None:
            self.compute_transform_matrix()
        
        warped = cv2.warpPerspective(
            image, self.M, 
            (self.board_size + 2 * self.threshold, 
             self.board_size + 2 * self.threshold)
        )
        return warped
    
    def inverse_transform(self, points: np.ndarray) -> np.ndarray:
        """Applies inverse transformation"""
        if self.M_inv is None:
            self.compute_transform_matrix()
        
        return cv2.perspectiveTransform(points, self.M_inv)


class ColorMask:
    # Define color ranges in HSV
    # Yellow: H ~20-40
    lower_yellow = np.array([15, 100, 100])
    upper_yellow = np.array([35, 255, 255])

    # Green: H ~40-90
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])

    @staticmethod
    def create_color_mask(image_rgb):
        """
        Creates a mask for yellow and green colors.
        Keeps only pixels with these colors, sets others to black.
        """
        # Convert RGB to HSV for better color detection
        hsv_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
        
        # Create masks for each color
        mask_yellow = cv2.inRange(hsv_image, ColorMask.lower_yellow, ColorMask.upper_yellow)
        mask_green = cv2.inRange(hsv_image, ColorMask.lower_green, ColorMask.upper_green)

        # Combine all masks
        combined_mask = cv2.bitwise_or(mask_yellow, mask_green)

        # Apply morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        
        # Apply mask to the original image
        masked_image = cv2.bitwise_and(image_rgb, image_rgb, mask=combined_mask)
        
        return masked_image, combined_mask
    
class ChessBoardSquares:
    ROWS, COLS = 8, 8
    def __init__(self, board_size: int):
        self.board_size = board_size
        self.square_width = board_size // self.COLS
        self.square_height = board_size // self.ROWS

    def get_square_region(self, warped_image: np.ndarray, square_index: int, 
                         padding_ratio: float = 0.2) -> np.ndarray:
        """Extracts the region of a specific square"""
        row = (square_index - 1) // self.COLS
        col = (square_index - 1) % self.COLS
        
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
        """Draws the 8x8 grid"""
        vis = image.copy()
        
        for i in range(self.ROWS):
            for j in range(self.COLS):
                top_left = (j * self.square_width, i * self.square_height)
                bottom_right = ((j + 1) * self.square_width, (i + 1) * self.square_height)
                cv2.rectangle(vis, top_left, bottom_right, color, thickness)
        
        return vis
    
    def get_all_squares_warped(self) -> list:
        """Returns the coordinates of all squares in order (starting from bottom-left)"""
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
    """Manages piece detection by pixel count"""
    
    def __init__(self, warped_image: np.ndarray, board_squares: ChessBoardSquares):
        self.warped_image = warped_image
        self.board_squares = board_squares
        # self.baseline_variance = None
        self.piece_place = [0] * 64
        self.piece_color = [0] * 64
    
    # def calculate_baseline_variance(self, empty_indices: list = None) -> float:
    #     """Calculates baseline variance of an empty square (kept for API compatibility)"""
    #     self.baseline_variance = 1.0  # Not used in pixel-count detection
    #     return self.baseline_variance
    
    def detect_piece_in_square(self, square_index: int, 
                              threshold_multiplier: float = 1.0,
                              min_pixel_ratio: float = 0.02) -> str:
        """Detects if a piece is present by counting non-black pixels in the masked image"""
        square_region = self.board_squares.get_square_region(self.warped_image, square_index, padding_ratio=0.33)
        
        # Count non-black pixels (color mask already isolates piece markers)
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
        """Detects the color of the piece"""
        square_region = self.board_squares.get_square_region(self.warped_image, square_index, padding_ratio=0.33)
        if square_region.shape[2] != 3:
            return 'empty'
        
        # Count non-black pixels (color mask already isolates piece markers)
        gray = cv2.cvtColor(square_region, cv2.COLOR_RGB2GRAY) if len(square_region.shape) == 3 else square_region
        non_black_count = np.count_nonzero(gray > 10)
        total_pixels = gray.shape[0] * gray.shape[1]

        if total_pixels == 0:
            return 'empty'
        
        ratio = non_black_count / total_pixels


        if ratio < min_pixel_ratio:
            return 'empty'
        
        hsv_region = cv2.cvtColor(square_region.astype(np.uint8), cv2.COLOR_RGB2HSV)
        hsv_colored = hsv_region[gray > 10]  # Only consider non-black pixels
        
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
    
    def detect_all_pieces(self, ratio: float = 0.02):
        """Detects all pieces on the board"""
        # if self.baseline_variance is None:
        #     self.calculate_baseline_variance()
        
        for i in range(1, 65):
            color = self._get_piece_color(i, ratio)
            
            if color != 'empty':
                self.piece_place[i-1] = 1
                self.piece_color[i-1] = color
                # print(f"Square {i}: PIECE DETECTED with color {color}")
            else:
                self.piece_place[i-1] = 0


# ============================================================================
# CLASS: MoveDetection
# ============================================================================
class MoveDetection:
    """Manages move detection"""
    
    def __init__(self, chess_game):
        self.chess_game = chess_game
        self.old_piece_place = [0] * 64
        self.old_piece_color = [0] * 64
        self.move_start = 0
        self.move_end = 0
        
    def init_from_board(self):
        """Initialize piece state from the current chess board"""
        board = self.chess_game.get_board()
        
        # Iterate through all 64 squares
        for square_index in range(64):
            piece = board.piece_at(square_index)
            
            if piece is None:
                # Empty square
                self.old_piece_place[square_index] = 0
                self.old_piece_color[square_index] = 0
            else:
                # Occupied square
                self.old_piece_place[square_index] = 1
                # Color: 0 for black/captured, use 1 for white, 2 for black (or map to 'white'/'black')
                # For compatibility with camera detection: 'yellow' or 'green'
                self.old_piece_color[square_index] = 'white' if piece.color == chess.WHITE else 'black'

    def detect_castling(self, new_piece_place: list, new_piece_color: list) -> dict:
        """Detects castling moves"""
        if (self.old_piece_place[0] and self.old_piece_place[4] and new_piece_place[2] and new_piece_place[3] 
            and not self.old_piece_place[1] and not self.old_piece_place[2] and not self.old_piece_place[3]):
            if self.old_piece_color[0] == self.old_piece_color[4] == new_piece_color[2] == new_piece_color[3]:
                return {'move_start': 1, 'move_end': 3, 'uci': 'e1c1'}  # Queenside castling
            
        if (self.old_piece_place[7] and self.old_piece_place[4] and new_piece_place[5] and new_piece_place[6] 
            and not self.old_piece_place[5] and not self.old_piece_place[6]):
            if self.old_piece_color[7] == self.old_piece_color[4] == new_piece_color[5] == new_piece_color[6]:
                return {'move_start': 8, 'move_end': 6, 'uci': 'e1g1'}  # Kingside castling
            
        if (self.old_piece_place[56] and self.old_piece_place[60] and new_piece_place[58] and new_piece_place[59] 
            and not self.old_piece_place[57] and not self.old_piece_place[58] and not self.old_piece_place[59]):
            if self.old_piece_color[56] == self.old_piece_color[60] == new_piece_color[58] == new_piece_color[59]:
                return {'move_start': 57, 'move_end': 59, 'uci': 'e8c8'}  # Queenside castling
            
        if (self.old_piece_place[63] and self.old_piece_place[60] and new_piece_place[61] and new_piece_place[62] 
            and not self.old_piece_place[61] and not self.old_piece_place[62]):
            if self.old_piece_color[63] == self.old_piece_color[60] == new_piece_color[61] == new_piece_color[62]:
                return {'move_start': 64, 'move_end': 62, 'uci': 'e8g8'}  # Kingside castling
    
    def detect_move(self, new_piece_place: list, new_piece_color: list) -> dict:
        """Detects moves by comparing with the previous state"""
        analyses = [0] * 64
        
        # # Reset move detection for this frame
        # self.move_start = 0
        # self.move_end = 0
        
        # Check for castling first
        castling_move = self.detect_castling(new_piece_place, new_piece_color)
        if castling_move is not None:
            return castling_move
        
        # Detect normal moves
        for i in range(len(new_piece_place)):
            analyses[i] = new_piece_place[i] + self.old_piece_place[i]
            
            if analyses[i] == 2 and self.old_piece_color[i] != new_piece_color[i]:
                self.move_end = i+1
            
            if analyses[i] == 1:
                if new_piece_place[i] == 1:
                    self.move_end = i+1
                else:
                    self.move_start = i+1
        
        uci_move = self.get_uci_move()
        
        return {
            'move_start': self.move_start,
            'move_end': self.move_end,
            'uci': uci_move
        }
    
    def get_uci_move(self) -> str:
        """Converts positions to UCI notation"""
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
        start_file = files[(self.move_start - 1) % 8]
        start_rank = ranks[(self.move_start - 1) // 8]
        end_file = files[(self.move_end - 1) % 8]
        end_rank = ranks[(self.move_end - 1) // 8]

        print(f"Detected move: {start_file}{start_rank}{end_file}{end_rank}")

        return f"{start_file}{start_rank}{end_file}{end_rank}"
        


class Cam:
    """Main class integrating all functionalities"""
    
    def __init__(self, chess_game, board_size: int = 1200, camera_id: int = 0, scale: float = 1.0):
        self.chess_game = chess_game
        self.board_size = board_size
        self.scale = scale
        self.camera_id = camera_id
        self.image_path = None
        
        self.calibration = None
        self.squares = ChessBoardSquares(board_size)
        self.move_detector = MoveDetection(chess_game)
        # Initialize move detector with current board state
        self.move_detector.init_from_board()
        self.piece_detector = None
        self.transform = None
        self.cap = None
    
    def initialize_camera(self, calibrate: bool = False):
        """Initializes the camera with maximum quality"""
        self.cap = cv2.VideoCapture("/dev/video4", cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            print("[ERROR] Unable to open the camera")
            return False
        
        # Increase resolution and quality
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce latency
        
        # Get the actual resolution
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("[INFO] Camera initialized successfully")
        # print(f"[INFO] Requested resolution: 1920x1080")
        print(f"[INFO] Actual resolution: {actual_width}x{actual_height}")
        
        # Let the camera stabilize (warm-up)
        print("[INFO] Stabilizing camera (2 seconds)...")
        for _ in range(10):
            self.cap.read()
      
        
        if calibrate:
            self.calibrate_from_camera()
        
        calibration_points = self.load_calibration()
        self.transform = ChessBoardTransform(calibration_points, self.board_size)
        self.transform.compute_transform_matrix()
        
        return True
    
    def calibrate_from_camera(self):
        """Launches calibration from camera on a single photo"""
        print("[INFO] Starting calibration from camera...")
        print("[INFO] Capturing a photo...")
        
        frame = self.capture_frame()
        if frame is None:
            print("[ERROR] Unable to capture from camera")
            return
        
        print("[INFO] Photo captured ✓")
        
        # Créer l'objet calibration
        self.calibration = ImageCalibration("camera", scale=self.scale)
        
        # Appeler calibrate() en passant le frame capturé
        self.calibration.calibrate(frame=frame)

    def load_calibration(self) -> dict:
        """Loads calibration points"""
        if self.calibration is None:
            self.calibration = ImageCalibration("camera")
        
        return self.calibration.load_calibration()
    
    def capture_frame(self, show: bool = False) -> np.ndarray:
        """Captures a frame from the camera"""
        if self.cap is None or not self.cap.isOpened():
            print("[ERROR] Camera is not initialized")
            return None
        
        # Flush the internal buffer to get the latest frame
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
        cv2.imwrite("captured_frame.jpg", frame)
        return frame
    
    def process_frame(self) -> dict:
        """Processes a frame captured from the camera"""
        frame = self.capture_frame()
        if frame is None:
            return None
        
        # Convertir en RGB (même flux que CamDetect)
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Appliquer transformation perspective
        warped = self.transform.apply_transform(rgb_image)
        
        # Appliquer masque couleur
        masked_warped, mask = ColorMask.create_color_mask(warped)
        
        # Détecter les pièces
        self.piece_detector = PieceDetection(masked_warped, self.squares)
        self.piece_detector.detect_all_pieces()
        
        # Detect moves
        move_info = self.move_detector.detect_move(
            self.piece_detector.piece_place,
            self.piece_detector.piece_color
        )
        
        return {
            'original_frame': frame,
            'warped_image': masked_warped,
            'piece_place': self.piece_detector.piece_place,
            'piece_color': self.piece_detector.piece_color,
            'move': move_info
        }
    
    def process_image(self, image_path: str = None) -> dict:
        """Processes an image (file or camera)"""
        if image_path:
            # Charger depuis un fichier
            orig_image = cv2.imread(image_path)
            rgb_image = cv2.cvtColor(orig_image, cv2.COLOR_BGR2RGB)
        else:
            # Capturer depuis la caméra
            return self.process_frame()
        
        # Appliquer transformation perspective
        warped = self.transform.apply_transform(rgb_image)
        
        # Appliquer masque couleur
        masked_warped, mask = ColorMask.create_color_mask(warped)
        
        # Détecter les pièces
        self.piece_detector = PieceDetection(masked_warped, self.squares)
        self.piece_detector.detect_all_pieces()
        
        # Détecter les mouvements
        move_info = self.move_detector.detect_move(
            self.piece_detector.piece_place,
            self.piece_detector.piece_color
        )
        
        return {
            'warped_image': masked_warped,
            'piece_place': self.piece_detector.piece_place,
            'piece_color': self.piece_detector.piece_color,
            'move': move_info
        }
    
    def release(self):
        """Releases the camera"""
        if self.cap is not None:
            self.cap.release()
            print("[INFO] Camera released")


# ============================================================================
# USAGE EXAMPLE
# ============================================================================
if __name__ == "__main__":
    # Import chess game module (adjust import based on your structure)
    import chess  # or from your_module import ChessGame
    
    # Create a chess game instance
    chess_game = chess.Board()
    
    # Option 1: Calibration from camera, then analyze a single frame
    cam = Cam(chess_game=chess_game, board_size=1200, camera_id=1)
    cam.initialize_camera(calibrate=False)
    
    # Analyser une photo capturée
    result = cam.process_image()
    
    if result:
        print("\n=== RESULTS ===")
        print(f"Pieces detected: {sum(result['piece_place'])}")
        print(f"UCI move: {result['move']['uci']}")
        
        # Display the analyzed image with grid
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
        
        # Display the analyzed image with grid
        display_image = cv2.cvtColor(result['warped_image'], cv2.COLOR_RGB2BGR)
        display_image_with_grid = cam.squares.draw_grid(display_image, color=(0, 255, 0), thickness=2)
        cv2.namedWindow("Analyzed Chessboard", cv2.WINDOW_NORMAL)
        cv2.imshow("Analyzed Chessboard", display_image_with_grid)
        cv2.resizeWindow("Analyzed Chessboard", display_image_with_grid.shape[1], display_image_with_grid.shape[0])
        print("[INFO] Press any key to close the image")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    

    cam.release()