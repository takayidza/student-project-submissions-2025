# stage4_unhealthy.py
import cv2
import numpy as np
import os

exg = np.load('output/exg_array.npy')

exg_norm = cv2.normalize(exg, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25,25))
blackhat = cv2.morphologyEx(exg_norm, cv2.MORPH_BLACKHAT, kernel)

_, unhealthy_mask = cv2.threshold(blackhat, 10, 255, cv2.THRESH_BINARY)

veg_mask = (exg_norm > np.percentile(exg_norm, 50)).astype(np.uint8) * 255
unhealthy_mask = cv2.bitwise_and(unhealthy_mask, veg_mask)

kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
unhealthy_mask = cv2.morphologyEx(unhealthy_mask, cv2.MORPH_OPEN, kernel_small)

cv2.imwrite('output/unhealthy_mask.png', unhealthy_mask)
print("Stage4 complete: Saved unhealthy region mask (output/unhealthy_mask.png).")
