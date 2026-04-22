import numpy as np

from hitresearch_sim.polarization.compositor import PolarizationCompositor
from hitresearch_sim.polarization.lut import LibRadtranLUTBuilder


def test_lut_builder_generates_valid_ranges(tmp_path) -> None:
    lut = LibRadtranLUTBuilder("/opt/libRadtran/bin/uvspec").build(
        solar_zenith_deg=40.0,
        solar_azimuth_deg=140.0,
        out_dir=tmp_path,
    )
    assert lut.dolp.shape == (180, 360)
    assert lut.aop.shape == (180, 360)
    assert np.all(lut.dolp >= 0.0)
    assert np.all(lut.dolp <= 1.0)


def test_compositor_samples_spatially_varying_lut(tmp_path) -> None:
    lut = LibRadtranLUTBuilder("/opt/libRadtran/bin/uvspec").build(
        solar_zenith_deg=30.0,
        solar_azimuth_deg=90.0,
        out_dir=tmp_path,
    )
    upward = np.zeros((64, 64, 3), dtype=np.uint8)
    sky_mask = np.ones((64, 64), dtype=np.uint8)
    pol = PolarizationCompositor().compose(upward, sky_mask, lut)
    assert pol["dolp"].shape == (64, 64)
    assert np.std(pol["dolp"]) > 0.01
