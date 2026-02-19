import cv2
import numpy as np
import matplotlib.pyplot as plt 
import pandas as pd 
from ultralytics import YOLO
import  math
import ultralytics
import csv
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from ultralytics import YOLO
from PIL import Image
import os
import chess
import chess.svg
import json
import ctypes

## Extracting Chess Squares with Perspective Transformation ( image --> fen format)

# Path of Image that you want to convert
#image_path = r"test-14.jpeg"
#image_path = r"image2.jpg"
#image_path = r"image.png"
image_path = r"test1_jaune.jpg"

# === Load & Resize Image ===
scale = 0.3  # resize factor

# Define color ranges in HSV
# Yellow: H ~20-40
lower_yellow = np.array([15, 100, 100])
upper_yellow = np.array([35, 255, 255])

# Green: H ~40-90
lower_green = np.array([35, 50, 50])
upper_green = np.array([90, 255, 255])

orig_image = cv2.imread(image_path)




# read image and convert it to different color spaces 
image = cv2.resize(orig_image, None, fx=scale, fy=scale)
#image = cv2.imread(image_path)
gray_image=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
rgb_image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
#gray_image = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

## Processing Image  -->  OTSU Threshold , Canny edge detection , dilate , HoughLinesP 

# resized image for display

points = []


# === Mouse Callback ===
def mouse_click(event, x, y, flags, param):
    scale = param  # passed from setMouseCallback

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            # convert back to original coordinates
            orig_x = int(x / scale)
            orig_y = int(y / scale)

            points.append((orig_x, orig_y))
            print(f"[INFO] Point {len(points)}: {orig_x}, {orig_y}")
        else:
            print("[INFO] Already 4 points. Press 'r' to reset.")

def center_window(window_name, width, height):
    user32 = ctypes.windll.user32
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    x = (screen_w - width) // 2
    y = (screen_h - height) // 2

    cv2.moveWindow(window_name, x, y)

# === Calibration Function ===
def calibrate_board(image, scale):
    global points

    cv2.namedWindow("Kalibrasi Papan", cv2.WINDOW_NORMAL)

    # Afficher une première fois pour créer la fenêtre
    cv2.imshow("Kalibrasi Papan", image)

    # Centrer la fenêtre sans la redimensionner
    h, w = image.shape[:2]
    center_window("Kalibrasi Papan", w, h)

    cv2.setMouseCallback("Kalibrasi Papan", mouse_click, param=scale)


    while True:
        vis = image.copy()

        # draw clicked points (in resized coordinates)
        for idx, (ox, oy) in enumerate(points):
            x = int(ox * scale)
            y = int(oy * scale)

            cv2.circle(vis, (x, y), 6, (0, 0, 255), -1)
            cv2.putText(vis, str(idx+1), (x+8, y-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

        cv2.imshow("Kalibrasi Papan", vis)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('r'):
            print("[INFO] Reset points")
            points = []

        if len(points) == 4:
            break

    cv2.destroyAllWindows()

    # Save calibration points
    calibration_points = {
        "top_left": points[0],
        "top_right": points[1],
        "bottom_right": points[2],
        "bottom_left": points[3]
    }

    with open('calibration_points.json', 'w') as f:
        json.dump(calibration_points, f, indent=4)

    print("[INFO] Calibration saved to calibration_points.json")


# === Run Calibration ===
#calibrate_board(image, scale)


# Initialize variables to store extreme points
top_left = None
top_right = None
bottom_left = None
bottom_right = None
# Draw the contour and the extreme points

#calibrate_board(image, scale)

def read_calibration_points(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

calibration_points = read_calibration_points('calibration_points.json')

top_left = tuple(calibration_points["top_left"])
top_right = tuple(calibration_points["top_right"])
bottom_right = tuple(calibration_points["bottom_right"])
bottom_left = tuple(calibration_points["bottom_left"])



#### Apply Perspective Transformation
 
# read image and convert it to different color spaces 
image = cv2.imread(image_path)
rgb_image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

# Define the four source points (replace with actual coordinates)
extreme_points_list = np.float32([top_left, top_right, bottom_left, bottom_right])

threshold = 0  # Extra space on all sides

width, height = 1200 , 1200 

# Define the destination points (shifted by 'threshold' on all sides)
dst_pts = np.float32([
    [threshold, threshold], 
    [width + threshold, threshold], 
    [threshold, height + threshold], 
    [width + threshold, height + threshold]
])

# Compute the perspective transform matrix
M = cv2.getPerspectiveTransform(extreme_points_list, dst_pts)

# Apply the transformation with extra width and height
warped_image = cv2.warpPerspective(rgb_image, M, (width + 2 * threshold, height + 2 * threshold))

# === Create Color Mask for Yellow, Green, and Pink ===
def create_color_mask(image_rgb):
    """
    Creates a mask for yellow, and green
    Keeps only pixels with these colors, sets others to black.
    """
    # Convert RGB to HSV for better color detection
    hsv_image = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    
    # Create masks for each color
    mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
    mask_green = cv2.inRange(hsv_image, lower_green, upper_green)

    
    # Combine all masks
    combined_mask = cv2.bitwise_or(mask_yellow, mask_green)

    # Apply morphological operations to clean up the mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
    
    # Apply mask to the original image
    masked_image = cv2.bitwise_and(image_rgb, image_rgb, mask=combined_mask)
    
    return masked_image, combined_mask

# Apply the color mask to warped_image
warped_image_masked, mask = create_color_mask(warped_image)

# # Optional: Display the mask and masked image for verification
# cv2.imshow("Color Mask (jaune/vert/rose)", mask)
# cv2.imshow("Warped Image with Color Mask", cv2.cvtColor(warped_image_masked, cv2.COLOR_RGB2BGR))
# cv2.waitKey(0)

# Use the masked image for further processing
warped_image = warped_image_masked

cv2.circle(warped_image, (threshold, threshold), 15, (0, 0, 255), -1)   
cv2.circle(warped_image, (width + threshold, threshold), 15, (0, 0, 255), -1)   
cv2.circle(warped_image, (threshold, height + threshold), 15, (0, 0,255), -1)  
cv2.circle(warped_image, (width + threshold, height + threshold), 15, (0, 0, 255), -1)   



#### Divide board to 64 square

# Assuming area_warped is already defined
# Define number of squares (8x8 for chessboard)
rows, cols = 8, 8

# Calculate the width and height of each square
square_width = width // cols
square_height = height // rows

# Draw the squares on the warped image
for i in range(rows):
    for j in range(cols):
        # Calculate top-left and bottom-right corners of each square
        top_left = (j * square_width, i * square_height)
        bottom_right = ((j + 1) * square_width, (i + 1) * square_height)
        
        # Draw a rectangle for each square
        cv2.rectangle(warped_image, top_left, bottom_right, (0, 255, 0), 4)  # Green color, thickness 2




#### Display extracted squares on original image with inverse transformation
  
# read image and convert it to different color spaces 
image = cv2.imread(image_path)
rgb_image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)

# Compute the inverse perspective transformation matrix
M_inv = cv2.invert(M)[1]  # Get the inverse of the perspective matrix

rows, cols = 8, 8  # 8x8 chessboard

# Calculate the width and height of each square in the warped image
square_width = width // cols
square_height = height // rows

# List to store squares' data in the correct order (bottom-left first)
squares_data_warped = []

for i in range(rows - 1, -1, -1):  # Start from bottom row and move up
    for j in range(cols):  # Left to right order
        # Define the 4 corners of each square
        top_left = (j * square_width, i * square_height)
        top_right = ((j + 1) * square_width, i * square_height)
        bottom_left = (j * square_width, (i + 1) * square_height)
        bottom_right = ((j + 1) * square_width, (i + 1) * square_height)

        # Calculate center of the square
        x_center = (top_left[0] + bottom_right[0]) // 2
        y_center = (top_left[1] + bottom_right[1]) // 2

        # Append to list in the correct order
        squares_data_warped.append([
            (x_center, y_center),
            bottom_right,
            top_right,
            top_left,
            bottom_left
        ])

# Convert to numpy array for transformation
squares_data_warped_np = np.array(squares_data_warped, dtype=np.float32).reshape(-1, 1, 2)

# Transform all points back to the original image
squares_data_original_np = cv2.perspectiveTransform(squares_data_warped_np, M_inv)

# Reshape back to list format
squares_data_original = squares_data_original_np.reshape(-1, 5, 2)  # (num_squares, 5 points, x/y)


for square in squares_data_original:
    x_center, y_center = tuple(map(int, square[0]))  # Convert to int
    bottom_right = tuple(map(int, square[1]))
    top_right = tuple(map(int, square[2]))
    top_left = tuple(map(int, square[3]))
    bottom_left = tuple(map(int, square[4]))

    # Draw necessary lines only (to form grid)
    cv2.line(rgb_image, top_left, top_right, (0, 255, 0), 6)  # Top line
    cv2.line(rgb_image, top_left, bottom_left, (0, 255, 0), 6)  # Left line

    # Draw bottom and right lines only for last row/column
    if j == cols - 1:
        cv2.line(rgb_image, top_right, bottom_right, (0, 255, 0), 8)  # Right line
    if i == 0:
        cv2.line(rgb_image, bottom_left, bottom_right, (0, 255, 0), 8)  # Bottom line

cv2.circle(rgb_image, (int(extreme_points_list[0][0]),int(extreme_points_list[0][1])), 25, (255, 255, 255), -1)   
cv2.circle(rgb_image,  (int(extreme_points_list[1][0]),int(extreme_points_list[1][1])), 25, (255, 255, 255), -1)   
cv2.circle(rgb_image,  (int(extreme_points_list[2][0]),int(extreme_points_list[2][1])), 25, (255, 255,255), -1)   
cv2.circle(rgb_image,  (int(extreme_points_list[3][0]),int(extreme_points_list[3][1])), 25, (255, 255, 255), -1)   



#### Write coordinate of squares to a csv file

# Write coordinates to CSV file 
with open('board-square-positions-demo.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # columns
    writer.writerow(['x1', 'y1', 'x2', 'y2', 'x3', 'y3', 'x4', 'y4'])


    for coordinate in squares_data_original:
        center, bottom_right, top_right, top_left, bottom_left = coordinate
        
        writer.writerow([
                bottom_right[0], bottom_right[1],  # x1, y1
                top_right[0], top_right[1],        # x2, y2
                top_left[0], top_left[1],          # x3, y3
                bottom_left[0], bottom_left[1]     # x4, y4
            ])


#### Check coordinates of squares that are inside of CSV file

# Check CSV coordinates
data = pd.read_csv("board-square-positions-demo.csv") # true Coordinatesa

# Read the image

image = cv2.imread(image_path) 

# Loop through each row in the DataFrame and draw polygons
for i, row in data.iterrows():
    pts = []
    for j in range(0, 8, 2):
        pts.append((int(row.iloc[j]), int(row.iloc[j+1])))
    pts = np.array(pts, np.int32)
    pts = pts.reshape((-1,1,2))
    cv2.circle(image, (int(squares_data_original[i][0][0]),int(squares_data_original[i][0][1])), 3, (0,255,0), 3)
    cv2.polylines(image,[pts],True,(255,255,255),thickness=8)  # Change color and thickness as needed


# plt.figure(figsize=(10,8))
# plt.imshow(image)
# plt.show()
# for creating csv files for coordinates --> Chess-Board/Board_to_csv.ipynb
coordinates=pd.read_csv("board-square-positions-demo.csv")
coordinates.tail()



# dictionary for every cell's boundary coordinates 
# [[334, 1231], [344, 1139], [262, 1137], [247, 1228]] -->x1,y1,x2,y2,x3,y3,x4,y4
# 64 cell_value in total --> 8x8 board
coord_dict={}

cell=1
for row in coordinates.values:
    coord_dict[cell]=[[row[0],row[1]],[row[2],row[3]],[row[4],row[5]],[row[6],row[7]]]
    cell+=1
    

# class values , these values are decided before training
names: ['black-bishop', 'black-king', 'black-knight', 'black-pawn', 'black-queen', 'black-rook', 'white-bishop', 'white-king', 'white-knight', 'white-pawn', 'white-queen', 'white-rook'] # type: ignore
class_dict={0:'black-bishop',1:'black-king',2:'black-knight',3:'black-pawn',4: 'black-queen',5: 'black-rook',
            6:'white-bishop',7:'white-king',8: 'white-knight',9: 'white-pawn',10: 'white-queen',11:'white-rook'}

print("\n\n") 

        
game_list=[1, 11], [2, 8], [3, 6], [4, 10], [5, 7], [6, 6], [7, 8], [8, 11], [9, 9], [10, 9], [11, 9], [12, 9], [13, 9], [14, 9], [15, 9], [16, 9], [49, 3], [50, 3], [51, 3], [52, 3], [53, 3], [54, 3], [55, 3], [56, 3], [57, 5], [58, 2], [59, 0], [60, 4], [61, 1], [62, 0], [63, 2], [64, 5]

# show game , if cell value exist in game_list , then print piece in that cell , otherwise print space 
chess_str=""
for i in range(1, 65):
    
    for slist in game_list:
        if slist[0] == i:
            print(class_dict[slist[1]], end=" ")
            chess_str+=f" {class_dict[slist[1]]} "
            break
    else:
        print("space", end=" ")
        chess_str+=" space "

    if i % 8 == 0:
        print("\n")
        chess_str+="\n"

def get_empty_square_baseline_variance(warped_image):
    """
    Calcule la variance moyenne d'une case vide (sans pièce).
    Une case vide a une variance faible (couleur uniforme).
    """
    rows, cols = 8, 8
    square_width = warped_image.shape[1] // cols
    square_height = warped_image.shape[0] // rows
    
    # Prendre plusieurs cases vides (au milieu du plateau)
    empty_squares_indices = [18, 20, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44, 46, 48, 19, 21, 25, 27, 29, 31, 35, 37, 39, 41, 43, 45, 47, 49]
    
    
    empty_variances = []
    for idx in empty_squares_indices:
        row = (idx - 1) // 8
        col = (idx - 1) % 8
        
        square_region = warped_image[
            row * square_height : (row + 1) * square_height,
            col * square_width : (col + 1) * square_width
        ]
        
        variance = np.var(square_region)
        empty_variances.append(variance)
    
    baseline_variance = np.median(empty_variances)
    print(f"Baseline variance (case vide): {baseline_variance:.2f}")
    return baseline_variance


def is_piece_in_square_variance(warped_image, square_index, baseline_variance, threshold_multiplier=1.0):
    """
    Détecte une pièce en comparant la variance avec le baseline des cases vides.
    Si variance > baseline * threshold_multiplier, il y a une pièce.
    """
    rows, cols = 8, 8
    square_width = warped_image.shape[1] // cols
    square_height = warped_image.shape[0] // rows
    
    row = (square_index - 1) // 8
    col = (square_index - 1) % 8
    
    # Extraire la case complète
    full_region = warped_image[
        row * square_height : (row + 1) * square_height,
        col * square_width : (col + 1) * square_width
    ]
    
    # Calculer le padding en pixels
    pad_height = int(square_height * 0.2)
    pad_width = int(square_width * 0.2)
    
    # Extraire seulement la partie intérieure (sans les bordures)
    square_region = full_region[
        pad_height : square_height - pad_height,
        pad_width : square_width - pad_width
    ]


    blurred_square = cv2.GaussianBlur(square_region, (5, 5), 0)
    variance = np.var(blurred_square)
  
    ratio = variance / baseline_variance if baseline_variance > 0 else 0
    
    #print(f"Square {square_index}: variance={variance:.2f}, ratio={ratio:.2f}", end="")
    
    if ratio > threshold_multiplier:
        #print(" ✓ PIECE DETECTED")
        return get_piece_color(square_region)
    else:
        #print(" ✗ VIDE (couleur uniforme)")
        return False


def get_piece_color(square_region):
    """
    Détecte la couleur de la pièce en analysant uniquement les pixels non-noirs.
    square_region est en RGB.
    Returns: 'yellow', 'green', ou 'empty'
    """
    # Convert RGB to HSV for better color detection
    if square_region.shape[2] != 3:
        return 'empty'
    
    # Create mask for non-black pixels (where R+G+B > 30)
    rgb_sum = np.sum(square_region, axis=2)
    non_black_mask = rgb_sum > 30
    
    # Count non-black pixels
    colored_pixel_count = np.sum(non_black_mask)
    
    if colored_pixel_count < 10:  # Need at least 10 colored pixels
        return 'empty'
    
    # Convert to HSV
    hsv_region = cv2.cvtColor(square_region.astype(np.uint8), cv2.COLOR_RGB2HSV)
    
    # Extract only non-black HSV values
    hsv_colored = hsv_region[non_black_mask]
    
    # Calculate mean HSV values only for colored pixels
    h_mean = np.mean(hsv_colored[:, 0])
    s_mean = np.mean(hsv_colored[:, 1])
    v_mean = np.mean(hsv_colored[:, 2])
    
    # Check if there's enough saturation (colored pixel)
    if s_mean < 30 or v_mean < 30:
        return 'empty'
    
    # Determine color based on Hue (0-180 in OpenCV)
    # Yellow: H ~20-40
    if 15 < h_mean < 40:
        return 'yellow'
    # Green: H ~40-100
    elif 40 <= h_mean < 100:
        return 'green'
    else:
        return 'unknown'



baseline_variance = get_empty_square_baseline_variance(warped_image)

print("\nDétection des pièces (par variance):\n")

old_piece_place = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 0]
old_piece_color= [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'yellow', 0, 0, 'yellow', 'yellow', 0, 'yellow', 'yellow', 'yellow', 0, 0]

new_piece_place = [0] * 64  # Initialize with 64 zeros
new_piece_color = [0] * 64  # To store detected piece color for each square
analyses = [0] * 64 
move_start = 0
move_end = 0

for i in range(1, 65):
    if is_piece_in_square_variance(warped_image, i, baseline_variance, threshold_multiplier=1.0) is not False:
        new_piece_color[i-1] = is_piece_in_square_variance(warped_image, i, baseline_variance, threshold_multiplier=1.0)
        new_piece_place[i-1] = 1
        print(f"Square {i}: PIECE DETECTED with color {new_piece_color[i-1]}")
    else:
        new_piece_place[i-1] = 0

print(new_piece_color)

for i in range(len(new_piece_place)):
    analyses[i] = new_piece_place[i] + old_piece_place[i]
    if analyses[i] == 2 and old_piece_color[i] != new_piece_color[i]:
        print(f"Square {i+1}: PIECE COLOR CHANGED from {old_piece_color[i]} to {new_piece_color[i]}")
        move_end = i+1
    if analyses[i] == 1:
        if new_piece_place[i] == 1:
            print(f"Square {i+1}: NEW PIECE DETECTED")
            move_end = i+1

        else:
            print(f"Square {i+1}: PIECE REMOVED")
            move_start = i+1


plt.imshow(warped_image)
plt.show()



def get_uci_move(move_start, move_end):
    files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

    start_file = files[(move_start - 1) % 8]
    start_rank = ranks[(move_start - 1) // 8]
    end_file = files[(move_end - 1) % 8]
    end_rank = ranks[(move_end - 1) // 8]

    return f"{start_file}{start_rank}{end_file}{end_rank}"
uci_move = get_uci_move(move_start, move_end)
print(f"Detected move in UCI format: {uci_move}")

# def parse_coordinates(input_str):
#     """
#     Parse the input string to extract the positions of the chess pieces.
#     """
#     rows = input_str.strip().split('\n')
#     chess_pieces = []
#     for row in rows:  # Reversing rows to invert ranks
#         pieces = row.strip().split()
#         chess_pieces.extend(pieces)
#     return chess_pieces



 
# input_str=chess_str

# chess_pieces = parse_coordinates(input_str)

# board = chess.Board(None)

# piece_mapping = {
#     'white-pawn': chess.PAWN,
#     'black-pawn': chess.PAWN,
#     'white-knight': chess.KNIGHT,
#     'black-knight': chess.KNIGHT,
#     'white-bishop': chess.BISHOP,
#     'black-bishop': chess.BISHOP,
#     'white-rook': chess.ROOK,
#     'black-rook': chess.ROOK,
#     'white-queen': chess.QUEEN,
#     'black-queen': chess.QUEEN,
#     'white-king': chess.KING,
#     'black-king': chess.KING,
#     'space': None
# }

# for rank in range(8):
#     for file in range(8):
#         piece = chess_pieces[rank * 8 + file]
#         if piece != 'space':
#             color = chess.WHITE if piece.startswith('white') else chess.BLACK
#             piece_type = piece_mapping[piece]
#             board.set_piece_at(chess.square(file, rank), chess.Piece(piece_type, color))  # Not inverting rank

# svgboard = chess.svg.board(board)
# with open("2Dboard.svg", "w") as f:
#     f.write(svgboard)

 

# # Function to convert SVG to PNG
# def convert_svg_to_png(svg_file_path, png_file_path):
#     # Read the SVG file and convert it to a ReportLab Drawing
#     drawing = svg2rlg(svg_file_path)
#     # Render the drawing to a PNG file
#     renderPM.drawToFile(drawing, png_file_path, fmt='jpeg')
#     print(f"Converted {svg_file_path} to {png_file_path}")

# # Example usage
# svg_file = '2Dboard.svg'
# png_file = 'Extracted-Board.jpeg'
# convert_svg_to_png(svg_file, png_file)

# original_image = cv2.imread(image_path)
# original_image=cv2.cvtColor(original_image,cv2.COLOR_BGR2RGB)
 



# plt.figure(figsize=(14, 10))  # Increase the figure size to 18x6 inches


# plt.subplot(131)
# plt.title(f"{image_path}")
# plt.imshow(original_image)

# plt.subplot(132)
# plt.title("Extracted Squares")
# plt.imshow(image)

# plt.subplot(133)
# plt.title("Converted Image")
# plt.imshow(cv2.cvtColor(cv2.imread(png_file),cv2.COLOR_BGR2RGB))

# # Save the figure as a PNG file
# output_path = 'output_figure.png'
# plt.savefig(output_path)

# plt.show()  
