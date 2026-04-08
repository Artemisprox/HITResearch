from __future__ import annotations

import numpy as np

from .lut import PolarizationLUT


class PolarizationCompositor:
    def compose(self, upward_rgb: np.ndarray, sky_mask: np.ndarray, lut: PolarizationLUT) -> dict[str, np.ndarray]:
        h, w = sky_mask.shape
        dolp_map = np.zeros((h, w), dtype=np.float32)
        aop_map = np.zeros((h, w), dtype=np.float32)
        dolp_map[sky_mask > 0] = lut.dolp[0, 0]
        aop_map[sky_mask > 0] = lut.aop[0, 0]
        return {
            "upward_rgb": upward_rgb,
            "sky_mask": sky_mask,
            "dolp": dolp_map,
            "aop": aop_map,
        }
