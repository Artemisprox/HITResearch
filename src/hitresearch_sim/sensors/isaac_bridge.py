from __future__ import annotations

from dataclasses import dataclass
import os
from datetime import datetime, timezone
from typing import Any

import numpy as np

from hitresearch_sim.sensors.stereo import StereoSensor


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
    _warmed_up: bool = False
    _attach_records: list[dict[str, str]] | None = None
    _attach_failures: list[dict[str, str]] | None = None
    _left_rp: Any = None
    _right_rp: Any = None
    _up_rp: Any = None
    _recent_errors: list[str] | None = None

    @property
    def _debug_enabled(self) -> bool:
        return os.environ.get("HITRESEARCH_ISAAC_DEBUG", "0") not in ("", "0", "false", "False")

    def _log(self, msg: str, *, force: bool = False) -> None:
        if not (force or self._debug_enabled):
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        print(f"[isaac_bridge][{ts}] {msg}")

    def _push_error(self, msg: str) -> None:
        if self._recent_errors is None:
            self._recent_errors = []
        self._recent_errors.append(msg)
        if len(self._recent_errors) > 100:
            self._recent_errors = self._recent_errors[-100:]

    @staticmethod
    def _extract_array(data: Any) -> np.ndarray:
        payload = data
        if isinstance(payload, dict):
            for key in ("data", "rgb", "image"):
                if key in payload:
                    payload = payload[key]
                    break

        if payload is None:
            raise RuntimeError("Annotator returned no image data.")

        if hasattr(payload, "numpy"):
            payload = payload.numpy()

        try:
            arr = np.asarray(payload)
        except Exception as exc:  # pragma: no cover - depends on Isaac runtime object type
            raise RuntimeError(f"Unable to convert annotator output to ndarray: {type(payload)!r}") from exc

        return arr

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
        self._left_rp = left_rp
        self._right_rp = right_rp
        self._up_rp = up_rp

        self._attach_records = []
        self._attach_failures = []
        self._recent_errors = []
        self._left_ann = self._attach_annotator(rep, left_rp, "stereo_left")
        self._right_ann = self._attach_annotator(rep, right_rp, "stereo_right")
        self._up_ann = self._attach_annotator(rep, up_rp, "upward")
        self._log(
            "render products created: "
            f"left={self._render_product_path(left_rp)}, "
            f"right={self._render_product_path(right_rp)}, "
            f"up={self._render_product_path(up_rp)}",
            force=True,
        )
        self._initialized = True

    def _enable_stereo_fallback(self, reason: str) -> None:
        if self._stereo_fallback is None:
            self._stereo_fallback = StereoSensor(self.stereo_width, self.stereo_height)
        self._stereo_mode = "synthetic_fallback"
        self._stereo_fallback_reason = reason
        print(f"[warn] Stereo capture switched to synthetic fallback: {reason}")

    @staticmethod
    def _render_product_path(render_product: Any) -> str:
        if isinstance(render_product, str):
            return render_product
        path = getattr(render_product, "path", None)
        if isinstance(path, str):
            return path
        return str(render_product)

    def _attach_annotator(self, rep: Any, render_product: Any, label: str) -> Any:
        rp_path = self._render_product_path(render_product)
        attempts: list[tuple[str, list[Any]]] = [
            ("LdrColor", [render_product]),
            ("LdrColor", [rp_path]),
            ("rgb", [render_product]),
            ("rgb", [rp_path]),
        ]
        errors: list[str] = []
        for annotator_name, target in attempts:
            try:
                ann = rep.AnnotatorRegistry.get_annotator(annotator_name)
                ann.attach(target)
            except Exception as exc:
                errors.append(f"{annotator_name}@{type(target[0]).__name__}:{exc}")
                if self._attach_failures is not None:
                    self._attach_failures.append(
                        {
                            "sensor": label,
                            "annotator": annotator_name,
                            "target_type": type(target[0]).__name__,
                            "target": str(target[0]),
                            "error": str(exc),
                        }
                    )
                continue

            if self._attach_records is not None:
                self._attach_records.append(
                    {
                        "sensor": label,
                        "annotator": annotator_name,
                        "target_type": type(target[0]).__name__,
                        "target": str(target[0]),
                    }
                )
            self._log(
                f"attach success sensor={label} annotator={annotator_name} target={type(target[0]).__name__}:{target[0]}"
            )
            return ann

        raise RuntimeError(
            f"Failed to attach annotator for {label} (render_product={rp_path}). Attempts: {' | '.join(errors)}"
        )

    @staticmethod
    def _update_app_once() -> None:
        try:
            import omni.kit.app
        except ImportError:
            return
        omni.kit.app.get_app().update()

    @staticmethod
    def _is_transient_frame_error(exc: Exception) -> bool:
        text = str(exc).lower()
        transient_markers = (
            "empty frame",
            "empty image",
            "unexpected annotator image shape: (0,)",
            "insufficient channels",
            "no image data",
        )
        return any(marker in text for marker in transient_markers)

    def _reattach_annotator(self, name: str) -> None:
        try:
            import omni.replicator.core as rep
        except ImportError:
            return

        if name == "stereo_left" and self._left_rp is not None:
            self._left_ann = self._attach_annotator(rep, self._left_rp, "stereo_left")
            self._log(f"reattach completed for {name}", force=True)
            return
        if name == "stereo_right" and self._right_rp is not None:
            self._right_ann = self._attach_annotator(rep, self._right_rp, "stereo_right")
            self._log(f"reattach completed for {name}", force=True)
            return
        if name == "upward" and self._up_rp is not None:
            self._up_ann = self._attach_annotator(rep, self._up_rp, "upward")
            self._log(f"reattach completed for {name}", force=True)
            return

    def _recreate_render_product_and_annotator(self, name: str) -> None:
        try:
            import omni.replicator.core as rep
        except ImportError:
            return

        if name == "stereo_left":
            rp = rep.create.render_product(self.stereo_left_prim, (self.stereo_width, self.stereo_height))
            self._left_rp = rp
            self._left_ann = self._attach_annotator(rep, rp, "stereo_left")
        elif name == "stereo_right":
            rp = rep.create.render_product(self.stereo_right_prim, (self.stereo_width, self.stereo_height))
            self._right_rp = rp
            self._right_ann = self._attach_annotator(rep, rp, "stereo_right")
        elif name == "upward":
            rp = rep.create.render_product(self.upward_prim, (self.upward_width, self.upward_height))
            self._up_rp = rp
            self._up_ann = self._attach_annotator(rep, rp, "upward")
        else:
            return
        self._log(f"recreated render product + annotator for {name}", force=True)
        self._update_app_once()
        self._update_app_once()

    def _read_bgr_with_retries(self, annotator: Any, name: str, retries: int = 20) -> np.ndarray:
        last_exc: Exception | None = None
        half_idx = max(1, retries) // 2
        recreate_idx = max(1, (max(1, retries) * 2) // 3)
        for idx in range(max(1, retries)):
            try:
                return self._to_bgr(annotator.get_data())
            except Exception as exc:
                last_exc = exc
                err_msg = f"{name} retry[{idx + 1}/{max(1, retries)}] {type(exc).__name__}: {exc}"
                self._push_error(err_msg)
                self._log(err_msg)
                if idx == half_idx and self._is_transient_frame_error(exc):
                    try:
                        self._log(f"attempting annotator reattach for {name} after transient failures", force=True)
                        self._reattach_annotator(name)
                    except Exception:
                        pass
                    next_ann = {
                        "stereo_left": self._left_ann,
                        "stereo_right": self._right_ann,
                        "upward": self._up_ann,
                    }.get(name, None)
                    if next_ann is not None:
                        annotator = next_ann
                if idx == recreate_idx and self._is_transient_frame_error(exc):
                    try:
                        self._log(f"attempting full render product recreation for {name}", force=True)
                        self._recreate_render_product_and_annotator(name)
                    except Exception as recreate_exc:
                        self._push_error(f"recreate failed for {name}: {recreate_exc}")
                    next_ann = {
                        "stereo_left": self._left_ann,
                        "stereo_right": self._right_ann,
                        "upward": self._up_ann,
                    }.get(name, None)
                    if next_ann is not None:
                        annotator = next_ann
                self._update_app_once()
        raise RuntimeError(f"Failed to read annotator '{name}' after {retries} retries: {last_exc}")

    @staticmethod
    def _to_bgr(img: np.ndarray) -> np.ndarray:
        arr = IsaacSensorBridge._extract_array(img)
        if arr.dtype.itemsize == 0:
            raise RuntimeError(
                f"Annotator returned unsupported dtype with zero itemsize: {arr.dtype!r}, shape={arr.shape}"
            )

        if arr.ndim != 3:
            if arr.size == 0:
                raise RuntimeError(f"Annotator returned empty frame: shape={arr.shape}, dtype={arr.dtype}")
            raise ValueError(f"Unexpected annotator image shape: {arr.shape}, dtype={arr.dtype}")

        if arr.shape[-1] < 3:
            raise RuntimeError(f"Annotator returned insufficient channels: shape={arr.shape}, dtype={arr.dtype}")

        rgb = arr[..., :3]
        if rgb.dtype.kind == "f":
            if rgb.size == 0:
                raise RuntimeError(f"Annotator returned empty float image data: shape={rgb.shape}, dtype={rgb.dtype}")
            scale = 255.0 if float(np.nanmax(rgb)) <= 1.0 else 1.0
            rgb = np.clip(rgb * scale, 0.0, 255.0)

        rgb = rgb.astype(np.uint8)
        if rgb.size == 0:
            raise RuntimeError(f"Annotator returned empty image data: shape={rgb.shape}, dtype={rgb.dtype}")
        return rgb[..., ::-1]

    def warmup(self, steps: int = 4) -> None:
        if self._warmed_up:
            return
        self._init_rgb_annotators()
        for _ in range(max(steps, 1)):
            self._update_app_once()
        # Validate one fetch to ensure render products are alive.
        if self._left_ann is not None and self._right_ann is not None:
            _ = self._read_bgr_with_retries(self._left_ann, "stereo_left")
            _ = self._read_bgr_with_retries(self._right_ann, "stereo_right")
        _ = self._read_bgr_with_retries(self._up_ann, "upward")
        self._warmed_up = True

    def capture_stereo(self) -> tuple[np.ndarray, np.ndarray]:
        self.warmup()
        if self._stereo_fallback is not None:
            return self._stereo_fallback.capture()
        try:
            left = self._read_bgr_with_retries(self._left_ann, "stereo_left")
            right = self._read_bgr_with_retries(self._right_ann, "stereo_right")
            return left, right
        except Exception as exc:
            self._enable_stereo_fallback(f"replicator stereo read failed: {exc}")
            return self._stereo_fallback.capture()

    def capture_upward(self) -> np.ndarray:
        self.warmup()
        return self._read_bgr_with_retries(self._up_ann, "upward")

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

    def diagnostics(self) -> dict[str, Any]:
        return {
            "stereo_left_prim": self.stereo_left_prim,
            "stereo_right_prim": self.stereo_right_prim,
            "upward_prim": self.upward_prim,
            "imu_prim": self.imu_prim,
            "attach_records": self._attach_records or [],
            "attach_failures": self._attach_failures or [],
            "left_render_product": self._render_product_path(self._left_rp) if self._left_rp is not None else "",
            "right_render_product": self._render_product_path(self._right_rp) if self._right_rp is not None else "",
            "up_render_product": self._render_product_path(self._up_rp) if self._up_rp is not None else "",
            "recent_errors": self._recent_errors or [],
        }
