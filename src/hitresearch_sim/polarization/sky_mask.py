from __future__ import annotations

import numpy as np


class SkyMaskExtractor:
    def extract(self, upward_rgb: np.ndarray) -> np.ndarray:
        b = upward_rgb[..., 0].astype(np.float32)
        g = upward_rgb[..., 1].astype(np.float32)
        r = upward_rgb[..., 2].astype(np.float32)
        mask = (b > 50.0) & (b > g * 1.05) & (b > r * 1.20)
        return mask.astype(np.uint8)
