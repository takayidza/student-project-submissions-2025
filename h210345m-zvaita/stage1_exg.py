import cv2
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

img = cv2.imread('./images/b.png')
b, g, r = cv2.split(img.astype(np.float32))

exg = 2 * g - (r + b)

exg_norm = (exg - exg.min()) / (exg.max() - exg.min() + 1e-6)

colors = ["red", "yellow", "green"]
cmap = LinearSegmentedColormap.from_list('RedGreen', colors, N=256)

heatmap = (cmap(exg_norm)[:, :, :3] * 255).astype(np.uint8)

os.makedirs('output', exist_ok=True)
cv2.imwrite('output/exg_heatmap.png', cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))
np.save('output/exg_array.npy', exg)

print("Stage1 complete: Saved ExG heatmap (output/exg_heatmap.png) and array (output/exg_array.npy).")
