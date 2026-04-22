import pytest
import numpy as np

from hitresearch_sim.sensors.isaac_bridge import IsaacSensorBridge


def test_bridge_raises_without_isaac_modules() -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=64,
        stereo_height=48,
        upward_width=64,
        upward_height=64,
    )
    with pytest.raises(RuntimeError, match="omni.replicator.core"):
        bridge.capture_stereo()


def test_bridge_intrinsics_shape() -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=80,
        stereo_height=60,
        upward_width=64,
        upward_height=64,
    )
    k = bridge.intrinsics()
    assert k["stereo"]["width"] == 80
    assert k["upward"]["width"] == 64


def test_to_bgr_validates_input() -> None:
    with pytest.raises(RuntimeError, match="no image data"):
        IsaacSensorBridge._to_bgr(None)
    arr = np.zeros((4, 4, 4), dtype=np.uint8)
    out = IsaacSensorBridge._to_bgr(arr)
    assert out.shape == (4, 4, 3)


def test_to_bgr_accepts_dict_float_payload() -> None:
    payload = {"data": np.ones((2, 3, 4), dtype=np.float32) * 0.5}
    out = IsaacSensorBridge._to_bgr(payload)
    assert out.shape == (2, 3, 3)
    assert out.dtype == np.uint8


def test_to_bgr_rejects_zero_itemsize_dtype() -> None:
    arr = np.empty((2, 2, 4), dtype=np.dtype("V0"))
    with pytest.raises(RuntimeError, match="zero itemsize"):
        IsaacSensorBridge._to_bgr(arr)


def test_read_bgr_with_retries_eventually_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=64,
        stereo_height=48,
        upward_width=64,
        upward_height=64,
    )

    class _Ann:
        def __init__(self) -> None:
            self.calls = 0

        def get_data(self):
            self.calls += 1
            if self.calls < 3:
                raise RuntimeError("temporary annotator failure")
            return np.zeros((2, 2, 4), dtype=np.uint8)

    monkeypatch.setattr(IsaacSensorBridge, "_update_app_once", staticmethod(lambda: None))
    out = bridge._read_bgr_with_retries(_Ann(), "test", retries=4)
    assert out.shape == (2, 2, 3)


def test_bridge_diagnostics_contains_prim_paths() -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=64,
        stereo_height=48,
        upward_width=64,
        upward_height=64,
    )
    diag = bridge.diagnostics()
    assert diag["stereo_left_prim"] == "/World/Drone/stereo_left"
    assert isinstance(diag["attach_records"], list)
    assert isinstance(diag["attach_failures"], list)


def test_capture_stereo_uses_fallback_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=32,
        stereo_height=24,
        upward_width=64,
        upward_height=64,
    )
    bridge._enable_stereo_fallback("test fallback")
    monkeypatch.setattr(IsaacSensorBridge, "warmup", lambda self: None)
    left, right = bridge.capture_stereo()
    assert left.shape == (24, 32, 3)
    assert right.shape == (24, 32, 3)


def test_capture_stereo_switches_to_fallback_on_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    bridge = IsaacSensorBridge(
        stereo_left_prim="/World/Drone/stereo_left",
        stereo_right_prim="/World/Drone/stereo_right",
        upward_prim="/World/Drone/upward_cam",
        imu_prim="/World/Drone/imu",
        stereo_width=32,
        stereo_height=24,
        upward_width=64,
        upward_height=64,
    )
    bridge._left_ann = object()
    bridge._right_ann = object()
    monkeypatch.setattr(IsaacSensorBridge, "warmup", lambda self: None)

    def _raise(*_args, **_kwargs):
        raise RuntimeError("replicator read failed")

    monkeypatch.setattr(IsaacSensorBridge, "_read_bgr_with_retries", lambda self, *_args, **_kwargs: _raise())
    left, right = bridge.capture_stereo()
    assert bridge._stereo_mode == "synthetic_fallback"
    assert "replicator stereo read failed" in bridge._stereo_fallback_reason
    assert left.shape == (24, 32, 3)
    assert right.shape == (24, 32, 3)
