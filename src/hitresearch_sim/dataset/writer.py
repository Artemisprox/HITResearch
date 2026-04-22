from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class DatasetWriter:
    def __init__(self, root: Path, sensor_meta: dict[str, Any] | None = None) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.rows: list[dict[str, Any]] = []
        if sensor_meta is not None:
            meta_path = self.root / "sensor_meta.json"
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(sensor_meta, f, ensure_ascii=False, indent=2)

    def write_frame(self, idx: int, payload: dict[str, Any]) -> None:
        frame_dir = self.root / f"frame_{idx:06d}"
        frame_dir.mkdir(parents=True, exist_ok=True)

        left_path = frame_dir / "stereo_left.png"
        right_path = frame_dir / "stereo_right.png"
        upward_path = frame_dir / "upward_rgb.png"
        sky_mask_path = frame_dir / "sky_mask.png"
        dolp_path = frame_dir / "dolp.npy"
        aop_path = frame_dir / "aop.npy"

        cv2.imwrite(str(left_path), payload["stereo_left"])
        cv2.imwrite(str(right_path), payload["stereo_right"])
        cv2.imwrite(str(upward_path), payload["upward_rgb"])
        cv2.imwrite(str(sky_mask_path), (payload["sky_mask"] * 255).astype(np.uint8))
        np.save(dolp_path, payload["dolp"])
        np.save(aop_path, payload["aop"])

        meta = payload["meta"]
        imu = meta.get("imu", {})
        health = meta.get("health", {})
        control = meta.get("control", {})

        row = {
            "frame_idx": idx,
            "t": meta.get("t"),
            "x": meta.get("x"),
            "y": meta.get("y"),
            "z": meta.get("z"),
            "yaw_deg": meta.get("yaw_deg"),
            "imu_ax": imu.get("ax"),
            "imu_ay": imu.get("ay"),
            "imu_az": imu.get("az"),
            "imu_gx": imu.get("gx"),
            "imu_gy": imu.get("gy"),
            "imu_gz": imu.get("gz"),
            "health_score": health.get("score"),
            "health_reason": health.get("reason"),
            "mode": meta.get("mode"),
            "ctrl_vx": control.get("vx"),
            "ctrl_vy": control.get("vy"),
            "ctrl_vz": control.get("vz"),
            "ctrl_yaw_rate": control.get("yaw_rate"),
            "stereo_left_path": str(left_path.relative_to(self.root)),
            "stereo_right_path": str(right_path.relative_to(self.root)),
            "upward_rgb_path": str(upward_path.relative_to(self.root)),
            "sky_mask_path": str(sky_mask_path.relative_to(self.root)),
            "dolp_path": str(dolp_path.relative_to(self.root)),
            "aop_path": str(aop_path.relative_to(self.root)),
        }
        self.rows.append(row)

    def finalize(self) -> None:
        if not self.rows:
            return
        csv_path = self.root / "dataset.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.rows[0].keys()))
            writer.writeheader()
            writer.writerows(self.rows)
