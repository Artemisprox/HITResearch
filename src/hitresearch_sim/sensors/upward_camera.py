from __future__ import annotations

import numpy as np


class UpwardCamera:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def capture(self) -> np.ndarray:
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
