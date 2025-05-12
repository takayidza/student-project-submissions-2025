# stage6_summary.py
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

orig = cv2.cvtColor(cv2.imread('./images/b.png'), cv2.COLOR_BGR2RGB)
exg_heatmap = cv2.cvtColor(cv2.imread('output/exg_heatmap.png'), cv2.COLOR_BGR2RGB)
anomaly = cv2.imread('output/anomaly_mask.png', 0)
path = cv2.imread('output/path_mask.png', 0)
unhealthy = cv2.imread('output/unhealthy_mask.png', 0)
# unet_mask = cv2.imread('output/unet_mask.png', 0)

fig, axes = plt.subplots(2, 3, figsize=(12, 8))
axes = axes.flatten()

titles = ['Original', 'ExG Heatmap', 'Anomaly Mask', 'Bare Areas', 'Unhealthy Mask', 'U-Net Mask']
images = [orig, exg_heatmap, anomaly, path, unhealthy]

for ax, img, title in zip(axes, images, titles):
    if img is None:
        ax.axis('off')
        continue
    if len(img.shape) == 2:  # grayscale masks
        ax.imshow(img, cmap='gray')
    else:  # RGB images
        ax.imshow(img)
    ax.set_title(title)
    ax.axis('off')

plt.tight_layout()
plt.savefig('output/summary.png')
print("Stage6 complete: Saved summary image (output/summary.png).")
