from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd


class DatasetWriter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = []

    def write_frame(self, idx: int, payload: dict[str, Any]) -> None:
        frame_dir = self.root / f"frame_{idx:06d}"
        frame_dir.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(str(frame_dir / "stereo_left.png"), payload["stereo_left"])
        cv2.imwrite(str(frame_dir / "stereo_right.png"), payload["stereo_right"])
        cv2.imwrite(str(frame_dir / "upward_rgb.png"), payload["upward_rgb"])
        cv2.imwrite(str(frame_dir / "sky_mask.png"), (payload["sky_mask"] * 255).astype(np.uint8))
        np.save(frame_dir / "dolp.npy", payload["dolp"])
        np.save(frame_dir / "aop.npy", payload["aop"])

        meta = payload["meta"]
        with (frame_dir / "meta.json").open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        self.records.append(meta)

    def finalize(self) -> None:
        pd.DataFrame(self.records).to_csv(self.root / "trajectory_gt.csv", index=False)
