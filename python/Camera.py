# Python program to identify
# color in images

# Importing the libraries OpenCV and numpy
import cv2
import numpy as np

# Read the images
img = cv2.imread("captured_image.png")

# Resizing the image
# image = cv2.resize(img, (700, 600))

# Convert Image to Image HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Defining lower and upper bound HSV values
lower1 = np.array([20, 120, 70])
upper1 = np.array([30, 255, 255])
mask1 = cv2.inRange(hsv, lower1, upper1)

lower2 = np.array([100, 100, 100])
upper2 = np.array([130, 255, 255])
mask2 = cv2.inRange(hsv, lower2, upper2)

mask = mask1 + mask2

# Display Image and Mask
cv2.imshow("Image", img)
cv2.imshow("Mask", mask)
cv2.imshow("Mask1", mask1)
cv2.imshow("Mask2", mask2)

# Make python sleep for unlimited time
cv2.waitKey(0)
