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

## Extracting Chess Squares with Perspective Transformation ( image --> fen format)

# Path of Image that you want to convert
#image_path = r"test-14.jpeg"
#image_path = r"image2.jpg"
image_path = r"image.png"



# read image and convert it to different color spaces 
image = cv2.imread(image_path)
gray_image=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
rgb_image=cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
#gray_image = cv2.imread(image, cv2.IMREAD_GRAYSCALE)

## Processing Image  -->  OTSU Threshold , Canny edge detection , dilate , HoughLinesP 


#### Find 4 extreme point of chess board

# Initialize variables to store extreme points
top_left = None
top_right = None
bottom_left = None
bottom_right = None
# Draw the contour and the extreme points

top_left= (162,85)
top_right= (701,86)
bottom_left= (96, 567)
bottom_right= (769,568)
# Mark the extreme points


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


plt.figure(figsize=(10,8))
plt.imshow(image)
plt.show()
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

# YOLOv8  model  
model = YOLO("chess-model-yolov8m.pt") 

# make prediction
results = model(image_path) # path to test image
im_array = results[0].plot(); # plot a BGR numpy array of predictions

print("\n\n") 

# list for cell number and piece id (class value)
game_list=[]

for result in results:  # results is model's prediction     
    for id,box in enumerate(result.boxes.xyxy) : # box with xyxy format, (N, 4)
            
            x1,y1,x2,y2=int(box[0]),int(box[1]),int(box[2]),int(box[3]) # take coordinates 

            # find middle of bounding boxes for x and y 
            x_mid=int((x1+x2)/2) 
            # add padding to y values
            y_mid=int((y1+y2)/2)+25

            for cell_value, coordinates in coord_dict.items():
                x_values = [point[0] for point in coordinates]
                y_values = [point[1] for point in coordinates]
                 
                if (min(x_values) <= x_mid <= max(x_values)) and (min(y_values) <= y_mid <= max(y_values)):
                    a=int(result.boxes.cls[id])

                    print(f" cell :  {cell_value} --> {a} ")
                    # add cell values and piece cell_value(class value
                    game_list.append([cell_value,a]) 
                    break

print("\n\n\n")        

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
 

def parse_coordinates(input_str):
    """
    Parse the input string to extract the positions of the chess pieces.
    """
    rows = input_str.strip().split('\n')
    chess_pieces = []
    for row in rows:  # Reversing rows to invert ranks
        pieces = row.strip().split()
        chess_pieces.extend(pieces)
    return chess_pieces

 
input_str=chess_str

chess_pieces = parse_coordinates(input_str)

board = chess.Board(None)

piece_mapping = {
    'white-pawn': chess.PAWN,
    'black-pawn': chess.PAWN,
    'white-knight': chess.KNIGHT,
    'black-knight': chess.KNIGHT,
    'white-bishop': chess.BISHOP,
    'black-bishop': chess.BISHOP,
    'white-rook': chess.ROOK,
    'black-rook': chess.ROOK,
    'white-queen': chess.QUEEN,
    'black-queen': chess.QUEEN,
    'white-king': chess.KING,
    'black-king': chess.KING,
    'space': None
}

for rank in range(8):
    for file in range(8):
        piece = chess_pieces[rank * 8 + file]
        if piece != 'space':
            color = chess.WHITE if piece.startswith('white') else chess.BLACK
            piece_type = piece_mapping[piece]
            board.set_piece_at(chess.square(file, rank), chess.Piece(piece_type, color))  # Not inverting rank

svgboard = chess.svg.board(board)
with open("extracted-data/2Dboard.svg", "w") as f:
    f.write(svgboard)

 

# Function to convert SVG to PNG
def convert_svg_to_png(svg_file_path, png_file_path):
    # Read the SVG file and convert it to a ReportLab Drawing
    drawing = svg2rlg(svg_file_path)
    # Render the drawing to a PNG file
    renderPM.drawToFile(drawing, png_file_path, fmt='jpeg')
    print(f"Converted {svg_file_path} to {png_file_path}")

# Example usage
svg_file = 'extracted-data/2Dboard.svg'
png_file = 'extracted-data/Extracted-Board.jpeg'
convert_svg_to_png(svg_file, png_file)

original_image = cv2.imread(image_path)
original_image=cv2.cvtColor(original_image,cv2.COLOR_BGR2RGB)
 



plt.figure(figsize=(14, 10))  # Increase the figure size to 18x6 inches


plt.subplot(131)
plt.title(f"{image_path}")
plt.imshow(original_image)

plt.subplot(132)
plt.title("Extracted Squares")
plt.imshow(image)

plt.subplot(133)
plt.title("Converted Image")
plt.imshow(cv2.cvtColor(cv2.imread(png_file),cv2.COLOR_BGR2RGB))

# Save the figure as a PNG file
output_path = 'output_figure.png'
plt.savefig(output_path)

plt.show()  
