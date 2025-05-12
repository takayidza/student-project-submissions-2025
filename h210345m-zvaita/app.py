# app.py

import streamlit as st
import subprocess, sys
from pathlib import Path
import cv2, numpy as np, pandas as pd
from matplotlib import pyplot as plt


SCRIPTS = [
    "stage1_exg.py",
    "stage3_path.py",
    "stage4_unhealthy.py",
    "stage5_unet.py",
    "stage6_summary.py",
    "stage7_grid_summary.py",
    "stage8_timeseries.py",
]

for script in SCRIPTS:
    try:
        subprocess.run([sys.executable, script], check=True)
    except Exception as e:
        st.error(f"Error running {script}: {e}")
        st.stop()


def load_img(path: Path, as_gray: bool=False):
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE if as_gray else cv2.IMREAD_COLOR)
    if img is None:
        return None
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB) if not as_gray else img


st.sidebar.title("🌽 Maize Field Dashboard")
stage = st.sidebar.radio("Select View", [
    "Original & Summary",
    "1) ExG Heatmap",
    "2) Anomaly Mask",
    "3) Path Mask",
    "4) Unhealthy Patches",
    # "5) U-Net Segmentation",
    "5) Canopy Cover (%)",
    "6) Grid Summary",
    "7) Time Series"
])

IMG_DIR = Path("images")
OUT_DIR = Path("output")
orig_path = IMG_DIR / "b.png"
orig_img = load_img(orig_path)

if orig_img is None:
    st.error("No source image found at `images/b.png`. Ensure your scripts saved it correctly.")
    st.stop()



if stage == "Original & Summary":
    st.header("Original Field Image")
    st.image(orig_img, use_column_width=True)
    st.header("Combined Summary")
    summary = load_img(OUT_DIR / "summary.png")
    st.image(summary, use_column_width=True)

elif stage == "1) ExG Heatmap":
    st.header("Excess Green (ExG) Heatmap")
    heat = load_img(OUT_DIR / "exg_heatmap.png")
    st.image(orig_img, use_column_width=True)
    st.image(heat, use_column_width=True)
    exg_arr = np.load(OUT_DIR / "exg_array.npy")
    # st.subheader("ExG Value Distribution")
    # fig, ax = plt.subplots()
    # ax.hist(exg_arr.flatten(), bins=50, color='g', alpha=0.7)
    # ax.set_xlabel("ExG value"); ax.set_ylabel("Frequency")
    # st.pyplot(fig)

elif stage == "2) Anomaly Mask":
    st.header("Anomalies (Very Low Green Areas)")
    mask = load_img(OUT_DIR / "anomaly_mask.png", as_gray=True)
    st.image(orig_img, use_column_width=True)
    st.image(mask, use_column_width=True, clamp=True)

elif stage == "3) Path Mask":
    st.header("Paths & Bare Areas")
    mask = load_img(OUT_DIR / "path_mask.png", as_gray=True)
    st.image(orig_img, use_column_width=True)
    st.image(mask, use_column_width=True, clamp=True)

elif stage == "4) Unhealthy Patches":
    st.header("Unhealthy (Stressed) Patches")
    mask = load_img(OUT_DIR / "unhealthy_mask.png", as_gray=True)
    st.image(orig_img, use_column_width=True)
    st.image(mask, use_column_width=True, clamp=True)

# elif stage == "5) U-Net Segmentation":
#     st.header("U-Net Vegetation Segmentation")
#     mask = load_img(OUT_DIR / "unet_mask.png", as_gray=True)
#     st.image(mask, use_column_width=True, clamp=True)

elif stage == "5) Canopy Cover (%)":
    st.header("Canopy Coverage Percentage")
    opt = st.selectbox("Mask to compute from", ["inverted Path mask", "U-Net mask"])
    if opt == "U-Net mask":
        mask = load_img(OUT_DIR / "unet_mask.png", as_gray=True) > 0
    else:
        bare = load_img(OUT_DIR / "path_mask.png", as_gray=True)
        mask = bare == 0
    pct = mask.sum() / mask.size * 100
    ori_img = load_img(OUT_DIR / "path_mask.png")
    st.metric("Canopy Cover", f"{pct:.2f}%")
    st.image(ori_img, use_column_width=True)

elif stage == "6) Grid Summary":
    st.header("Grid-based ExG Summary")

    st.markdown(
        """
        **How to read this grid map:**  
        - We’ve divided your field image into a 5×5 grid of “cells.”  
        - Each cell shows the **average Excess Green (ExG)** value—our proxy for vegetation vigor.  
        - **High ExG (darker green)** means lush, healthy growth; **low ExG (reddish)** signals areas needing attention.  
        - Use this map to spot underperforming patches quickly and target fertilization or irrigation.  
        """
    )

    csv_path = OUT_DIR / "grid_summary.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        st.dataframe(df)
        pivot = df.pivot(index="row", columns="col", values="mean_exg")
        fig, ax = plt.subplots()
        c = ax.imshow(pivot.values, cmap="RdYlGn")
        fig.colorbar(c, ax=ax, label="Mean ExG")
        ax.set_xlabel("Grid Col"); ax.set_ylabel("Grid Row")
        st.pyplot(fig)
    else:
        st.warning("`grid_summary.csv` not found in output/")

elif stage == "7) Time Series":
    st.header("Time-Series of Average ExG")
    ts_csv = OUT_DIR / "timeseries.csv"
    ts_img = OUT_DIR / "timeseries.png"
    if ts_csv.exists():
        ts = pd.read_csv(ts_csv)
        fig, ax = plt.subplots()
        ax.plot(ts["time"], ts["mean_exg"], marker='o')
        ax.set_xlabel("Time"); ax.set_ylabel("Mean ExG")
        st.pyplot(fig)
        st.dataframe(ts)
    elif ts_img.exists():
        st.image(load_img(ts_img))
    else:
        st.warning("No time series outputs found in output/")

st.sidebar.markdown("---")
st.sidebar.write("⚙️ Built with Streamlit")
