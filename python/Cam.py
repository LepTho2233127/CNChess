import cv2
import numpy as np
import json
import ctypes

## Extracting Chess Squares with Perspective Transformation ( image --> fen format)

class ImageCalibration:
    
    def __init__(self, image_path: str, scale: float = 1.0):
        self.image_path = image_path
        self.scale = scale
        self.points = []
        self.calibration_file = 'calibration_points.json'
        
    def mouse_click(self, event, x, y, flags, param):
        """Callback pour les clics souris"""
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
        """Centre la fenêtre sur l'écran"""
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
        """Lance la calibration interactive (depuis fichier ou frame caméra)"""
        if frame is not None:
            # Utiliser le frame passé en paramètre
            image = cv2.resize(frame, None, fx=self.scale, fy=self.scale)
            print("[INFO] Photo capturée depuis la caméra")
        else:
            # Charger depuis le fichier
            orig_image = cv2.imread(self.image_path)
            image = cv2.resize(orig_image, None, fx=self.scale, fy=self.scale)
            print("[INFO] Image chargée depuis le fichier")
        
        cv2.namedWindow("Calibration Plateau", cv2.WINDOW_NORMAL)
        
        h, w = image.shape[:2]
        self.center_window("Calibration Plateau", w, h)
        
        cv2.setMouseCallback("Calibration Plateau", self.mouse_click, param=self.scale)
        
        print("[INFO] Cliquez sur les 4 coins du plateau (haut-gauche, haut-droit, bas-gauche, bas-droit)")
        print("[INFO] Appuyez sur 'R' pour réinitialiser ou attendez que les 4 points soient détectés")
        
        first_display = True
        
        while True:
            vis = image.copy()
            
            # Dessiner les points
            for idx, (ox, oy) in enumerate(self.points):
                x = int(ox * self.scale)
                y = int(oy * self.scale)
                cv2.circle(vis, (x, y), 6, (0, 0, 255), -1)
                cv2.circle(vis, (x, y), 8, (255, 255, 255), 2)  # Bordure blanche
                cv2.putText(vis, str(idx+1), (x+8, y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            cv2.imshow("Calibration Plateau", vis)
            cv2.resizeWindow("Calibration Plateau", vis.shape[1], vis.shape[0])
            if first_display:
                print("[INFO] Photo affichée - en attente de clics sur les coins")
                first_display = False
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('r'):
                print("[INFO] Réinitialisation des points")
                self.points = []
            elif key == ord('q'):
                print("[INFO] Calibration annulée")
                cv2.destroyAllWindows()
                return
            
            if len(self.points) == 4:
                print("[INFO] 4 points détectés ✓")
                break
        
        cv2.destroyAllWindows()
        print("[INFO] Calibration complétée")
        self.save_calibration()
    
    def save_calibration(self):
        """Sauvegarde les points de calibration en JSON"""
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
        """Charge les points de calibration depuis JSON"""
        with open(self.calibration_file, 'r') as f:
            return json.load(f)


class ChessBoardTransform:
    """Gère la transformation perspective du plateau"""

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
        """Calcule la matrice de transformation perspective"""
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
        """Applique la transformation perspective"""
        if self.M is None:
            self.compute_transform_matrix()
        
        warped = cv2.warpPerspective(
            image, self.M, 
            (self.board_size + 2 * self.threshold, 
             self.board_size + 2 * self.threshold)
        )
        return warped
    
    def inverse_transform(self, points: np.ndarray) -> np.ndarray:
        """Applique la transformation inverse"""
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
    # === Create Color Mask for Yellow, Green, and Pink ===
    def create_color_mask(image_rgb):
        """
        Creates a mask for yellow, and green
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
        """Extrait la région d'une case spécifique"""
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
        """Dessine la grille 8x8"""
        vis = image.copy()
        
        for i in range(self.ROWS):
            for j in range(self.COLS):
                top_left = (j * self.square_width, i * self.square_height)
                bottom_right = ((j + 1) * self.square_width, (i + 1) * self.square_height)
                cv2.rectangle(vis, top_left, bottom_right, color, thickness)
        
        return vis
    
    def get_all_squares_warped(self) -> list:
        """Retourne les coordonnées de todas les cases en ordre (bas-gauche d'abord)"""
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
    """Gère la détection des pièces par variance"""
    
    def __init__(self, warped_image: np.ndarray, board_squares: ChessBoardSquares):
        self.warped_image = warped_image
        self.board_squares = board_squares
        # self.baseline_variance = None
        self.piece_place = [0] * 64
        self.piece_color = [0] * 64
    
    # def calculate_baseline_variance(self, empty_indices: list = None) -> float:
    #     """Calcule la variance baseline d'une case vide (kept for API compatibility)"""
    #     self.baseline_variance = 1.0  # Not used in pixel-count detection
    #     return self.baseline_variance
    
    def detect_piece_in_square(self, square_index: int, 
                              threshold_multiplier: float = 1.0,
                              min_pixel_ratio: float = 0.02) -> str:
        """Détecte si une pièce est présente by counting non-black pixels in the masked image"""
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

        square_region = self.board_squares.get_square_region(self.warped_image, square_index, padding_ratio=0.33)

        """Détecte la couleur de la pièce"""
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
        """Détecte toutes les pièces du plateau"""
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
    """Gère la détection des mouvements"""
    
    def __init__(self):
        self.old_piece_place = [0] * 64
        self.old_piece_color = [0] * 64
        self.move_start = 0
        self.move_end = 0
    
    def detect_move(self, new_piece_place: list, new_piece_color: list) -> dict:
        """Détecte les mouvements par comparaison avec l'état précédent"""
        analyses = [0] * 64
        
        for i in range(len(new_piece_place)):
            analyses[i] = new_piece_place[i] + self.old_piece_place[i]
            
            if analyses[i] == 2 and self.old_piece_color[i] != new_piece_color[i]:
                # print(f"Square {i+1}: PIECE COLOR CHANGED from {self.old_piece_color[i]} to {new_piece_color[i]}")
                self.move_end = i+1
            
            if analyses[i] == 1:
                if new_piece_place[i] == 1:
                    # print(f"Square {i+1}: NEW PIECE DETECTED")
                    self.move_end = i+1
                else:
                    # print(f"Square {i+1}: PIECE REMOVED")
                    self.move_start = i+1
        
        # Mettre à jour l'état
        self.old_piece_place = new_piece_place
        self.old_piece_color = new_piece_color
        
        uci_move = self.get_uci_move()
        
        return {
            'move_start': self.move_start,
            'move_end': self.move_end,
            'uci': uci_move
        }
    
    def get_uci_move(self) -> str:
        """Convertit les positions en notation UCI"""
        files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        ranks = ['8', '7', '6', '5', '4', '3', '2', '1']
        start_file = files[(self.move_start - 1) % 8]
        start_rank = ranks[(self.move_start - 1) // 8]
        end_file = files[(self.move_end - 1) % 8]
        end_rank = ranks[(self.move_end - 1) // 8]

        print(f"Detected move: {start_file}{start_rank}{end_file}{end_rank}")

        return f"{start_file}{start_rank}{end_file}{end_rank}"
        


class Cam:
    """Classe principale intégrant toutes les fonctionnalités"""
    
    def __init__(self, board_size: int = 1200, camera_id: int = 0, scale: float = 1.0):
        self.board_size = board_size
        self.scale = scale
        self.camera_id = camera_id
        self.image_path = None
        
        self.calibration = None
        self.squares = ChessBoardSquares(board_size)
        self.move_detector = MoveDetection()
        self.piece_detector = None
        self.transform = None
        self.cap = None
    
    def initialize_camera(self, calibrate: bool = False):
        """Initialise la caméra avec qualité maximale"""
        self.cap = cv2.VideoCapture("/dev/video4", cv2.CAP_V4L2)
        
        if not self.cap.isOpened():
            print("[ERROR] Impossible d'ouvrir la caméra")
            return False
        
        # Augmenter la résolution et la qualité
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Réduire la latence
        
        # Récupérer la résolution réelle
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print("[INFO] Caméra initialisée avec succès")
        # print(f"[INFO] Résolution demandée: 1920x1080")
        print(f"[INFO] Résolution réelle: {actual_width}x{actual_height}")
        
        # Laisser la caméra se stabiliser (warm-up)
        print("[INFO] Stabilisation de la caméra (2 secondes)...")
        for _ in range(10):
            self.cap.read()
      
        
        if calibrate:
            self.calibrate_from_camera()
        
        calibration_points = self.load_calibration()
        self.transform = ChessBoardTransform(calibration_points, self.board_size)
        self.transform.compute_transform_matrix()
        
        return True
    
    def calibrate_from_camera(self):
        """Lance la calibration depuis la caméra sur une photo unique"""
        print("[INFO] Démarrage de la calibration depuis la caméra...")
        print("[INFO] Capture d'une photo...")
        
        frame = self.capture_frame()
        if frame is None:
            print("[ERROR] Impossible de capturer depuis la caméra")
            return
        
        print("[INFO] Photo capturée ✓")
        
        # Créer l'objet calibration
        self.calibration = ImageCalibration("camera", scale=self.scale)
        
        # Appeler calibrate() en passant le frame capturé
        self.calibration.calibrate(frame=frame)

    def load_calibration(self) -> dict:
        """Charge les points de calibration"""
        if self.calibration is None:
            self.calibration = ImageCalibration("camera")
        
        return self.calibration.load_calibration()
    
    def capture_frame(self, show: bool = False) -> np.ndarray:
        """Capture une frame depuis la caméra"""
        if self.cap is None or not self.cap.isOpened():
            print("[ERROR] La caméra n'est pas initialisée")
            return None
        
        # Flush the internal buffer to get the latest frame
        for _ in range(5):
            self.cap.grab()
        
        ret, frame = self.cap.retrieve()
        if not ret:
            print("[ERROR] Impossible de lire depuis la caméra")
            return None
        if show:
            cv2.namedWindow("Frame brut capturé", cv2.WINDOW_NORMAL)
            cv2.imshow("Frame brut capturé", frame)
            cv2.resizeWindow("Frame brut capturé", frame.shape[1], frame.shape[0])
        return frame
    
    def process_frame(self) -> dict:
        """Traite une frame capturée depuis la caméra"""
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
        
        # Détecter les mouvements
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
        """Traite une image (fichier ou caméra)"""
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
        """Libère la caméra"""
        if self.cap is not None:
            self.cap.release()
            print("[INFO] Caméra libérée")


# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================
if __name__ == "__main__":
    # Option 1: Calibration depuis la caméra, puis analyser une frame unique
    cam = Cam(board_size=1200, camera_id=1)
    cam.initialize_camera(calibrate=False)
    
    # Analyser une photo capturée
    result = cam.process_image()
    
    if result:
        print("\n=== RÉSULTATS ===")
        print(f"Pièces détectées: {sum(result['piece_place'])}")
        print(f"Mouvement UCI: {result['move']['uci']}")
        
        # Afficher l'image analysée avec grille
        display_image = cv2.cvtColor(result['warped_image'], cv2.COLOR_RGB2BGR)
        display_image_with_grid = cam.squares.draw_grid(display_image, color=(0, 255, 0), thickness=2)
        cv2.namedWindow("Plateau d'échecs analysé", cv2.WINDOW_NORMAL)
        cv2.imshow("Plateau d'échecs analysé", display_image_with_grid)
        cv2.resizeWindow("Plateau d'échecs analysé", display_image_with_grid.shape[1], display_image_with_grid.shape[0])
        print("[INFO] Appuyez sur une touche pour fermer l'image")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    result = cam.process_image()
    
    if result:
        print("\n=== RÉSULTATS ===")
        print(f"Pièces détectées: {sum(result['piece_place'])}")
        print(f"Mouvement UCI: {result['move']['uci']}")
        
        # Afficher l'image analysée avec grille
        display_image = cv2.cvtColor(result['warped_image'], cv2.COLOR_RGB2BGR)
        display_image_with_grid = cam.squares.draw_grid(display_image, color=(0, 255, 0), thickness=2)
        cv2.namedWindow("Plateau d'échecs analysé", cv2.WINDOW_NORMAL)
        cv2.imshow("Plateau d'échecs analysé", display_image_with_grid)
        cv2.resizeWindow("Plateau d'échecs analysé", display_image_with_grid.shape[1], display_image_with_grid.shape[0])
        print("[INFO] Appuyez sur une touche pour fermer l'image")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    

    cam.release()