# # Python program to identify
# # color in images

# # Importing the libraries OpenCV and numpy
# import cv2
# import numpy as np

# # Read the images
# img = cv2.imread("captured_image.png")

# # Resizing the image
# # image = cv2.resize(img, (700, 600))

# # Convert Image to Image HSV
# hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# # Defining lower and upper bound HSV values
# lower1 = np.array([20, 120, 70])
# upper1 = np.array([30, 255, 255])
# mask1 = cv2.inRange(hsv, lower1, upper1)

# lower2 = np.array([100, 100, 100])
# upper2 = np.array([130, 255, 255])
# mask2 = cv2.inRange(hsv, lower2, upper2)

# mask = mask1 + mask2

# # Display Image and Mask
# cv2.imshow("Image", img)
# cv2.imshow("Mask", mask)
# cv2.imshow("Mask1", mask1)
# cv2.imshow("Mask2", mask2)

# # Make python sleep for unlimited time
# cv2.waitKey(0)
# import cv2

# cap = cv2.VideoCapture(0)   # 0 = première caméra

# if not cap.isOpened():
#     print("Impossible d'ouvrir la caméra")
#     exit()

# ret, frame = cap.read()
# cap.release()

# if not ret:
#     print("Impossible de capturer l'image")
#     exit()

# # Sauvegarde optionnelle
# cv2.imwrite("photo.png", frame)


# # Affichage
# gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
# blur = cv2.GaussianBlur(gray, (5,5), 0)
# cv2.imshow("Photo", blur)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

import cv2
import numpy as np
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--rotate", type=int, default=0,
                    choices=[0, 90, 180, 270],
                    help="Rotasi orientasi papan terhadap kamera (CW). "
                         "Misal kamera dari kanan = 90, dari belakang = 180, dari kiri = 270.")
args = parser.parse_args()
CAM_ROT = args.rotate

points = []

def mouse_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append((x, y))
            print(f"[INFO] Titik {len(points)}: {x}, {y}")
        else:
            print("[INFO] Sudah 4 titik. Tekan 'r' untuk reset atau 's' untuk simpan.")

def remap_index(r_disp, c_disp, cam_rot):
    """Remap index (baris, kolom) dari tampilan kamera ke notasi papan standar."""
    if cam_rot == 0:
        r_std, c_std = r_disp, c_disp
    elif cam_rot == 90:
        r_std, c_std = c_disp, 7 - r_disp
    elif cam_rot == 180:
        r_std, c_std = 7 - r_disp, 7 - c_disp
    elif cam_rot == 270:
        r_std, c_std = 7 - c_disp, r_disp
    else:
        r_std, c_std = r_disp, c_disp
    return r_std, c_std

# === Buka kamera ===
# cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
# if not cap.isOpened():
#     exit()
image_path = r"image.png"



# read image and convert it to different color spaces 
image = cv2.imread(image_path)
cv2.namedWindow("Kalibrasi Papan")
cv2.setMouseCallback("Kalibrasi Papan", mouse_click)


while True:
    #ret, frame = cap.read()
    #ret, 
    frame = image

    # if not ret:
    #     continue

    vis = frame.copy()

    # Gambar titik klik
    for idx, p in enumerate(points):
        cv2.circle(vis, p, 6, (0, 0, 255), -1)
        cv2.putText(vis, str(idx+1), (p[0]+8, p[1]-8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    if len(points) == 4:
        # Gambar kotak & grid
        pts = np.array(points, dtype=np.int32)
        cv2.polylines(vis, [pts], True, (255,255,255), 2)

        src = np.array([[0,0],[8,0],[8,8],[0,8]], dtype=np.float32)
        dst = np.array(points, dtype=np.float32)
        H = cv2.getPerspectiveTransform(src, dst)

        src_grid = np.array([[[x,y] for x in range(9)] for y in range(9)], dtype=np.float32)
        dst_grid = cv2.perspectiveTransform(src_grid.reshape(-1,1,2), H).reshape(9,9,2)

        # Gambar grid
        for r in range(9):
            cv2.polylines(vis, [dst_grid[r,:,:].astype(int)], False, (180,180,180), 1)
        for c in range(9):
            cv2.polylines(vis, [dst_grid[:,c,:].astype(int)], False, (180,180,180), 1)

        # === Tampilkan label notasi papan standar ===
        files = 'abcdefgh'
        ranks = '87654321'
        font = cv2.FONT_HERSHEY_SIMPLEX

        for r in range(8):
            for c in range(8):
                r_std, c_std = remap_index(r, c, CAM_ROT)
                file_letter = files[c_std]
                rank_char = ranks[r_std]
                label = f"{file_letter}{rank_char}"

                center = dst_grid[r, c] + (dst_grid[r+1, c+1] - dst_grid[r, c]) / 2
                cx, cy = int(center[0]), int(center[1])
                cv2.putText(vis, label, (cx-12, cy+5), font, 0.5, (0,255,255), 1, cv2.LINE_AA)

    cv2.imshow("Kalibrasi Papan", vis)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print("Keluar tanpa menyimpan.")
        break
    elif key == ord('r'):
        points = []
        print("[INFO] Reset titik.")
    elif key == ord('s'):
        if len(points) != 4:
            print("[WARN] Harus klik 4 titik dulu sebelum menyimpan.")
            continue

        src = np.array([[0,0],[8,0],[8,8],[0,8]], dtype=np.float32)
        dst = np.array(points, dtype=np.float32)
        H = cv2.getPerspectiveTransform(src, dst)

        src_grid = np.array([[[x,y] for x in range(9)] for y in range(9)], dtype=np.float32)
        dst_grid = cv2.perspectiveTransform(src_grid.reshape(-1,1,2), H).reshape(9,9,2)

        displayed_squares = {}
        for r in range(8):
            for c in range(8):
                tl = dst_grid[r, c].tolist()
                tr = dst_grid[r, c+1].tolist()
                br = dst_grid[r+1, c+1].tolist()
                bl = dst_grid[r+1, c].tolist()
                displayed_squares[(r,c)] = [tl,tr,br,bl]

        # Remap orientasi papan ke notasi standar
        files = 'abcdefgh'
        ranks = '87654321'
        squares_std = {}
        for (r_disp, c_disp), poly in displayed_squares.items():
            r_std, c_std = remap_index(r_disp, c_disp, CAM_ROT)
            file_letter = files[c_std]
            rank_char = ranks[r_std]
            squares_std[f"{file_letter}{rank_char}"] = poly

        with open('sqdict.json', 'w') as f:
            json.dump(squares_std, f, indent=2)
        print(f"[✅] sqdict.json disimpan dengan rotasi orientasi {CAM_ROT}° (notasi sudah disesuaikan).")
        break

cap.release()
cv2.destroyAllWindows()

