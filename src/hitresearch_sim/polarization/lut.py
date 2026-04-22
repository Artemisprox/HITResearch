from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(slots=True)
class PolarizationLUT:
    dolp: np.ndarray
    aop: np.ndarray
    solar_zenith_deg: float
    solar_azimuth_deg: float


class LibRadtranLUTBuilder:
    def __init__(self, uvspec_bin: str) -> None:
        self.uvspec_bin = uvspec_bin

    def build(self, solar_zenith_deg: float, solar_azimuth_deg: float, out_dir: Path) -> PolarizationLUT:
        # Approximated clear-sky polarization pattern from Rayleigh scattering.
        # libRadtran integration can replace this model by parsing uvspec outputs.
        _ = (out_dir, self.uvspec_bin)
        zenith_deg = np.arange(180, dtype=np.float32)[:, None]
        azimuth_deg = np.arange(360, dtype=np.float32)[None, :]
        theta = np.deg2rad(zenith_deg)
        phi = np.deg2rad(azimuth_deg)
        theta_s = np.deg2rad(float(solar_zenith_deg))
        phi_s = np.deg2rad(float(solar_azimuth_deg))

        cos_gamma = (
            np.cos(theta) * np.cos(theta_s)
            + np.sin(theta) * np.sin(theta_s) * np.cos(phi - phi_s)
        )
        cos_gamma = np.clip(cos_gamma, -1.0, 1.0)
        sin2 = 1.0 - cos_gamma**2
        dolp = sin2 / (1.0 + cos_gamma**2 + 1e-6)
        dolp = np.clip(dolp, 0.0, 1.0).astype(np.float32)

        # AoP approximated as normal to scattering plane in local tangent frame.
        aop = 0.5 * np.arctan2(np.sin(2.0 * (phi - phi_s)), np.cos(2.0 * (phi - phi_s)))
        aop = (aop + 0.0 * theta).astype(np.float32)
        return PolarizationLUT(
            dolp=dolp,
            aop=aop,
            solar_zenith_deg=float(solar_zenith_deg),
            solar_azimuth_deg=float(solar_azimuth_deg),
        )
