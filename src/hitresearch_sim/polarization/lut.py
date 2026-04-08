from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(slots=True)
class PolarizationLUT:
    dolp: np.ndarray
    aop: np.ndarray


class LibRadtranLUTBuilder:
    def __init__(self, uvspec_bin: str) -> None:
        self.uvspec_bin = uvspec_bin

    def build(self, solar_zenith_deg: float, solar_azimuth_deg: float, out_dir: Path) -> PolarizationLUT:
        # TODO: invoke libRadtran uvspec and parse outputs physically.
        _ = (solar_zenith_deg, solar_azimuth_deg, out_dir)
        dolp = np.full((180, 360), 0.35, dtype=np.float32)
        aop = np.zeros((180, 360), dtype=np.float32)
        return PolarizationLUT(dolp=dolp, aop=aop)
