import cv2
import numpy as np

# Load bare‐area mask (paths)
bare_mask = cv2.imread('output/path_mask.png', cv2.IMREAD_GRAYSCALE)
if bare_mask is None:
    raise FileNotFoundError("Bare‐area mask not found.")

bare_bool = bare_mask > 0

bare_pixels = np.count_nonzero(bare_bool)
total_pixels = bare_mask.size

canopy_cover_pct = ((total_pixels - bare_pixels) / total_pixels) * 100
print(f"Canopy Cover Percentage: {canopy_cover_pct:.2f}%")
