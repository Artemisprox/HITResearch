from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ImuSample:
    ax: float
    ay: float
    az: float
    gx: float
    gy: float
    gz: float


class ImuSensor:
    def sample(self) -> ImuSample:
        return ImuSample(0.0, 0.0, -9.81, 0.0, 0.0, 0.0)
