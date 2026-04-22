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
