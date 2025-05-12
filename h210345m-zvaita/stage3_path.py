# stage3_path.py
import cv2
import numpy as np
import os

img = cv2.imread('./images/b.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

lower = np.array([0, 0, 180])
upper = np.array([30, 60, 255])
path_mask = cv2.inRange(hsv, lower, upper)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15,15))
path_clean = cv2.morphologyEx(path_mask, cv2.MORPH_CLOSE, kernel)
path_clean = cv2.morphologyEx(path_clean, cv2.MORPH_OPEN, kernel)

cv2.imwrite('output/path_mask.png', path_clean)
print("Stage3 complete: Saved path mask (output/path_mask.png).")
