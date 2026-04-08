#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Quick visualization for generated dataset.csv")
    parser.add_argument("--dataset-dir", required=True, help="Path to run_xxx folder containing dataset.csv")
    parser.add_argument("--frame-idx", type=int, default=0, help="Frame index for image snapshot")
    parser.add_argument("--save", default=None, help="Optional output image path")
    return parser.parse_args()


def read_img(dataset_dir: Path, rel_path: str) -> np.ndarray:
    img = cv2.imread(str(dataset_dir / rel_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Failed to read image: {dataset_dir / rel_path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def main() -> None:
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    csv_path = dataset_dir / "dataset.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"dataset.csv not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise RuntimeError("dataset.csv is empty")

    row = df.iloc[min(max(args.frame_idx, 0), len(df) - 1)]

    left = read_img(dataset_dir, row["stereo_left_path"])
    upward = read_img(dataset_dir, row["upward_rgb_path"])
    sky_mask = cv2.imread(str(dataset_dir / row["sky_mask_path"]), cv2.IMREAD_GRAYSCALE)
    dolp = np.load(dataset_dir / row["dolp_path"])

    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes = axes.flatten()

    axes[0].plot(df["x"], df["y"], color="tab:blue")
    axes[0].set_title("Trajectory XY")
    axes[0].set_xlabel("x (m)")
    axes[0].set_ylabel("y (m)")
    axes[0].axis("equal")

    axes[1].plot(df["t"], df["z"], color="tab:green")
    axes[1].set_title("Altitude vs Time")
    axes[1].set_xlabel("t (s)")
    axes[1].set_ylabel("z (m)")

    axes[2].plot(df["t"], df["yaw_deg"], color="tab:orange")
    axes[2].set_title("Yaw vs Time")
    axes[2].set_xlabel("t (s)")
    axes[2].set_ylabel("yaw (deg)")

    axes[3].imshow(left)
    axes[3].set_title(f"Stereo Left (frame={int(row['frame_idx'])})")
    axes[3].axis("off")

    axes[4].imshow(upward)
    axes[4].set_title("Upward RGB")
    axes[4].axis("off")

    axes[5].imshow(dolp, cmap="viridis", vmin=0.0, vmax=1.0)
    axes[5].contour((sky_mask > 0).astype(np.uint8), levels=[0.5], colors="white", linewidths=0.8)
    axes[5].set_title("DoLP + Sky Mask contour")
    axes[5].axis("off")

    fig.tight_layout()
    if args.save:
        out = Path(args.save)
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, dpi=140)
        print(f"Saved visualization: {out}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
