from __future__ import annotations

import cv2
import numpy as np


class SkyMaskExtractor:
    def extract(self, upward_rgb: np.ndarray) -> np.ndarray:
        hsv = cv2.cvtColor(upward_rgb, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (90, 0, 40), (140, 255, 255))
        return (mask > 0).astype(np.uint8)
