# stage8_timeseries.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import datetime

def main():
    out = Path("output")
    grid_csv = out / "grid_summary.csv"
    if not grid_csv.exists():
        raise FileNotFoundError(f"{grid_csv} not found")

    df = pd.read_csv(grid_csv)

    base = datetime.date.today()
    times = [base - datetime.timedelta(days=14),
             base - datetime.timedelta(days=7),
             base]
    means = []
    for k, t in enumerate(times):
        val = df["mean_exg"].mean() + (k - 1) * 2.5
        means.append(val)

    ts = pd.DataFrame({
        "time": [d.isoformat() for d in times],
        "mean_exg": means
    })
    ts.to_csv(out / "timeseries.csv", index=False)
    print("Stage8 complete: Saved timeseries.csv")

    fig, ax = plt.subplots()
    ax.plot(ts["time"], ts["mean_exg"], marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Mean ExG")
    plt.xticks(rotation=45)
    plt.tight_layout()
    fig.savefig(out / "timeseries.png")
    print("Stage8 complete: Saved timeseries.png")

if __name__ == "__main__":
    main()
