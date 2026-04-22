import pytest

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
