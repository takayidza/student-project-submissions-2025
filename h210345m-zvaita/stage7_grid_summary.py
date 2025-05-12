# stage7_grid_summary.py
import numpy as np
import pandas as pd
from pathlib import Path

def main():
    out = Path("output")
    exg_path = out / "exg_array.npy"
    if not exg_path.exists():
        raise FileNotFoundError(f"{exg_path} not found")
    exg = np.load(exg_path)

    ROWS, COLS = 5, 5
    h, w = exg.shape
    data = []

    for i in range(ROWS):
        for j in range(COLS):
            rs, re = i*(h//ROWS), (i+1)*(h//ROWS)
            cs, ce = j*(w//COLS), (j+1)*(w//COLS)
            cell = exg[rs:re, cs:ce]
            mean_val = float(np.mean(cell))
            data.append((i, j, mean_val))

    df = pd.DataFrame(data, columns=["row", "col", "mean_exg"])
    df.to_csv(out / "grid_summary.csv", index=False)
    print("Stage7 complete: Saved grid_summary.csv")

if __name__ == "__main__":
    main()
