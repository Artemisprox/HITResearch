from __future__ import annotations

import numpy as np


class UpwardCamera:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.frame_idx = 0

    def capture(self) -> np.ndarray:
        x = np.linspace(0.0, 1.0, self.width, dtype=np.float32)
        y = np.linspace(0.0, 1.0, self.height, dtype=np.float32)[:, None]
        phase = (self.frame_idx % 180) / 180.0

        sky_blue = np.clip(0.6 + 0.35 * (1.0 - y), 0.0, 1.0)
        sky_green = np.clip(0.35 + 0.25 * (1.0 - y), 0.0, 1.0)
        sky_red = np.clip(0.10 + 0.10 * (1.0 - y), 0.0, 1.0)
        img = np.stack((sky_blue + 0.0 * x, sky_green + 0.0 * x, sky_red + 0.0 * x), axis=-1)

        # light moving cloud-like pattern
        cloud = 0.08 * np.sin((x[None, :] * 10.0 + y * 6.0 + phase * np.pi * 2))
        img[:, :, 0] = np.clip(img[:, :, 0] + cloud, 0.0, 1.0)
        img[:, :, 1] = np.clip(img[:, :, 1] + cloud, 0.0, 1.0)

        # dark tree line to guarantee non-sky pixels in lower area
        horizon = int(self.height * 0.72)
        img[horizon:, :, 0] *= 0.35
        img[horizon:, :, 1] *= 0.45
        img[horizon:, :, 2] *= 0.30

        self.frame_idx += 1
        return (img * 255).astype(np.uint8)

    def intrinsics(self) -> dict[str, float | int | str]:
        cx = (self.width - 1) * 0.5
        cy = (self.height - 1) * 0.5
        return {
            "width": self.width,
            "height": self.height,
            "model": "fisheye_approx",
            "cx": float(cx),
            "cy": float(cy),
            "fov_deg": 180.0,
        }
