from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(slots=True)
class IsaacSensorBridge:
    stereo_left_prim: str
    stereo_right_prim: str
    upward_prim: str
    imu_prim: str
    stereo_width: int
    stereo_height: int
    upward_width: int
    upward_height: int

    _initialized: bool = False
    _left_ann: Any = None
    _right_ann: Any = None
    _up_ann: Any = None

    def _init_rgb_annotators(self) -> None:
        if self._initialized:
            return
        try:
            import omni.replicator.core as rep
        except ImportError as exc:
            raise RuntimeError(
                "Isaac sensor bridge requires omni.replicator.core. "
                "Use sensors.provider=mock outside Isaac environment."
            ) from exc

        left_rp = rep.create.render_product(self.stereo_left_prim, (self.stereo_width, self.stereo_height))
        right_rp = rep.create.render_product(self.stereo_right_prim, (self.stereo_width, self.stereo_height))
        up_rp = rep.create.render_product(self.upward_prim, (self.upward_width, self.upward_height))

        self._left_ann = rep.AnnotatorRegistry.get_annotator("rgb")
        self._right_ann = rep.AnnotatorRegistry.get_annotator("rgb")
        self._up_ann = rep.AnnotatorRegistry.get_annotator("rgb")
        self._left_ann.attach([left_rp])
        self._right_ann.attach([right_rp])
        self._up_ann.attach([up_rp])
        self._initialized = True

    @staticmethod
    def _to_bgr(img: np.ndarray) -> np.ndarray:
        if img.ndim != 3:
            raise ValueError(f"Unexpected annotator image shape: {img.shape}")
        rgb = img[..., :3].astype(np.uint8)
        return rgb[..., ::-1]

    def capture_stereo(self) -> tuple[np.ndarray, np.ndarray]:
        self._init_rgb_annotators()
        left = self._to_bgr(self._left_ann.get_data())
        right = self._to_bgr(self._right_ann.get_data())
        return left, right

    def capture_upward(self) -> np.ndarray:
        self._init_rgb_annotators()
        return self._to_bgr(self._up_ann.get_data())

    def sample_imu(self) -> dict[str, float]:
        # Placeholder: wire Isaac IMU API here when exact sensor plugin selection is fixed.
        # Returning deterministic zero-like output keeps downstream schema stable.
        _ = self.imu_prim
        return {"ax": 0.0, "ay": 0.0, "az": 9.81, "gx": 0.0, "gy": 0.0, "gz": 0.0}
