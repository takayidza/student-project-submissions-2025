# stage2_anomaly.py
import cv2
import numpy as np
import os

exg = np.load('output/exg_array.npy')


anomaly_mask = (exg < 0).astype(np.uint8) * 255


kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5,5))
anomaly_clean = cv2.morphologyEx(anomaly_mask, cv2.MORPH_OPEN, kernel)
anomaly_clean = cv2.morphologyEx(anomaly_clean, cv2.MORPH_CLOSE, kernel)


cv2.imwrite('output/anomaly_mask.png', anomaly_clean)
print("Stage2 complete: Saved anomaly mask (output/anomaly_mask.png).")
