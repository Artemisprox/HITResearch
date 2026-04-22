import numpy as np

from hitresearch_sim.polarization.sky_mask import SkyMaskExtractor
from hitresearch_sim.sensors.stereo import StereoSensor
from hitresearch_sim.sensors.upward_camera import UpwardCamera


def test_stereo_sensor_outputs_are_not_all_black() -> None:
    sensor = StereoSensor(width=64, height=48)
    left, right = sensor.capture()
    k = sensor.intrinsics()

    assert left.shape == (48, 64, 3)
    assert right.shape == (48, 64, 3)
    assert np.any(left > 0)
    assert np.any(right > 0)
    assert k["width"] == 64
    assert k["height"] == 48
    assert k["baseline_m"] > 0.0


def test_upward_and_sky_mask_contain_sky_and_non_sky() -> None:
    camera = UpwardCamera(width=64, height=48)
    upward = camera.capture()
    k = camera.intrinsics()

    mask = SkyMaskExtractor().extract(upward)

    assert upward.shape == (48, 64, 3)
    assert np.any(upward > 0)
    assert mask.shape == (48, 64)
    assert np.any(mask == 1)
    assert np.any(mask == 0)
    assert k["model"] == "fisheye_approx"
