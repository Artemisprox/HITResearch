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
    _imu_sensor: Any = None
    _imu_warned: bool = False

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
        if self._imu_sensor is None:
            try:
                from omni.isaac.sensor import IMUSensor
            except Exception:
                self._imu_sensor = False
            else:
                try:
                    self._imu_sensor = IMUSensor(prim_path=self.imu_prim, name="imu_bridge")
                except Exception:
                    self._imu_sensor = False

        if self._imu_sensor not in (None, False):
            try:
                frame = self._imu_sensor.get_current_frame()
                lin = frame.get("lin_acc", [0.0, 0.0, 9.81])
                ang = frame.get("ang_vel", [0.0, 0.0, 0.0])
                return {
                    "ax": float(lin[0]),
                    "ay": float(lin[1]),
                    "az": float(lin[2]),
                    "gx": float(ang[0]),
                    "gy": float(ang[1]),
                    "gz": float(ang[2]),
                }
            except Exception:
                pass

        if not self._imu_warned:
            print("[warn] Isaac IMU API unavailable, using fallback IMU values.")
            self._imu_warned = True
        return {"ax": 0.0, "ay": 0.0, "az": 9.81, "gx": 0.0, "gy": 0.0, "gz": 0.0}

    def intrinsics(self) -> dict[str, dict[str, float | int | str]]:
        fx = self.stereo_width * 0.9
        fy = self.stereo_height * 0.9
        return {
            "stereo": {
                "width": self.stereo_width,
                "height": self.stereo_height,
                "fx": float(fx),
                "fy": float(fy),
                "cx": float((self.stereo_width - 1) * 0.5),
                "cy": float((self.stereo_height - 1) * 0.5),
                "baseline_m": 0.16,
            },
            "upward": {
                "width": self.upward_width,
                "height": self.upward_height,
                "model": "fisheye_approx",
                "cx": float((self.upward_width - 1) * 0.5),
                "cy": float((self.upward_height - 1) * 0.5),
                "fov_deg": 180.0,
            },
        }
