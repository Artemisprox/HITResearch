from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(slots=True)
class TrajectoryPoint:
    t: float
    x: float
    y: float
    z: float
    yaw_deg: float


class TrajectoryGenerator:
    def __init__(self, radius_m: float, min_alt_m: float, max_alt_m: float) -> None:
        self.radius_m = radius_m
        self.min_alt_m = min_alt_m
        self.max_alt_m = max_alt_m

    def circular(self, duration_s: float, dt_s: float) -> list[TrajectoryPoint]:
        ts = np.arange(0.0, duration_s, dt_s)
        points: list[TrajectoryPoint] = []
        for t in ts:
            theta = 2.0 * np.pi * t / duration_s
            x = self.radius_m * np.cos(theta)
            y = self.radius_m * np.sin(theta)
            z = self.min_alt_m + (self.max_alt_m - self.min_alt_m) * 0.5
            yaw = np.rad2deg(theta + np.pi / 2.0)
            points.append(TrajectoryPoint(t=float(t), x=float(x), y=float(y), z=float(z), yaw_deg=float(yaw)))
        return points
