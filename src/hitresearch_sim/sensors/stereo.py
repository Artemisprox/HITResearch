from __future__ import annotations

import numpy as np


class StereoSensor:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def capture(self) -> tuple[np.ndarray, np.ndarray]:
        left = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        right = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        return left, right
