from __future__ import annotations

import numpy as np

from .lut import PolarizationLUT


class PolarizationCompositor:
    def compose(self, upward_rgb: np.ndarray, sky_mask: np.ndarray, lut: PolarizationLUT) -> dict[str, np.ndarray]:
        h, w = sky_mask.shape
        dolp_map = np.zeros((h, w), dtype=np.float32)
        aop_map = np.zeros((h, w), dtype=np.float32)

        yy, xx = np.mgrid[0:h, 0:w]
        cx = (w - 1) * 0.5
        cy = (h - 1) * 0.5
        dx = (xx - cx) / max(cx, 1.0)
        dy = (yy - cy) / max(cy, 1.0)
        r = np.sqrt(dx**2 + dy**2)
        r = np.clip(r, 0.0, 1.0)

        zenith_deg = np.clip(r * 90.0, 0.0, 179.0).astype(np.int32)
        azimuth_deg = ((np.rad2deg(np.arctan2(dy, dx)) + 360.0) % 360.0).astype(np.int32)

        sampled_dolp = lut.dolp[zenith_deg, azimuth_deg]
        sampled_aop = lut.aop[zenith_deg, azimuth_deg]
        dolp_map[sky_mask > 0] = sampled_dolp[sky_mask > 0]
        aop_map[sky_mask > 0] = sampled_aop[sky_mask > 0]
        return {
            "upward_rgb": upward_rgb,
            "sky_mask": sky_mask,
            "dolp": dolp_map,
            "aop": aop_map,
        }
