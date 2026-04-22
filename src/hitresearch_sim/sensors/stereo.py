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

        base = np.clip(0.2 + 0.6 * x + 0.2 * y + 0.2 * np.sin((x + phase) * np.pi * 3), 0.0, 1.0)
        green = np.clip(0.3 + 0.4 * y + 0.3 * np.cos((y + phase) * np.pi * 2) + 0.0 * x, 0.0, 1.0)
        red = np.clip(0.2 + 0.5 * (1.0 - x) + 0.3 * np.sin((x + y + phase) * np.pi), 0.0, 1.0)

        left = np.stack((base, green, red), axis=-1)
        left = (left * 255).astype(np.uint8)
        right = np.roll(left, shift=6, axis=1)
        right[:, :6] = left[:, :6] // 2
        self.frame_idx += 1
        return left, right
