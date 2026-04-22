from __future__ import annotations

import numpy as np


class StereoSensor:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.frame_idx = 0

    def capture(self) -> tuple[np.ndarray, np.ndarray]:
        x = np.linspace(0.0, 1.0, self.width, dtype=np.float32)
        y = np.linspace(0.0, 1.0, self.height, dtype=np.float32)[:, None]
        phase = (self.frame_idx % 120) / 120.0

        sky = y < 0.45
        ground = ~sky

        blue = np.where(
            sky,
            0.65 + 0.25 * (0.45 - y) / 0.45,
            0.20 + 0.08 * np.sin((x + phase) * np.pi * 4),
        )
        green = np.where(
            sky,
            0.45 + 0.15 * (0.45 - y) / 0.45,
            0.30 + 0.35 * (y - 0.45) / 0.55 + 0.08 * np.cos((x + phase) * np.pi * 6),
        )
        red = np.where(
            sky,
            0.18 + 0.04 * (0.45 - y) / 0.45,
            0.22 + 0.20 * (y - 0.45) / 0.55 + 0.04 * np.sin((x + y + phase) * np.pi * 3),
        )

        trunk_pattern = (np.sin((x + phase) * np.pi * 20) > 0.93).astype(np.float32)
        trunk_pattern = trunk_pattern * ground.astype(np.float32)
        red = np.clip(red + trunk_pattern * 0.18, 0.0, 1.0)
        green = np.clip(green + trunk_pattern * 0.08, 0.0, 1.0)
        blue = np.clip(blue - trunk_pattern * 0.06, 0.0, 1.0)

        left = np.stack((blue, green, red), axis=-1)
        left = (left * 255).astype(np.uint8)
        right = np.roll(left, shift=6, axis=1)
        right[:, :6] = left[:, :6] // 2
        self.frame_idx += 1
        return left, right

    def intrinsics(self) -> dict[str, float | int]:
        fx = self.width * 0.9
        fy = self.height * 0.9
        cx = (self.width - 1) * 0.5
        cy = (self.height - 1) * 0.5
        return {
            "width": self.width,
            "height": self.height,
            "fx": float(fx),
            "fy": float(fy),
            "cx": float(cx),
            "cy": float(cy),
            "baseline_m": 0.16,
        }
