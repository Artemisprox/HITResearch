from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class GeoReference:
    origin_lat_deg: float
    origin_lon_deg: float
    origin_alt_m: float

    def enu_to_lla(self, east_m: float, north_m: float, up_m: float) -> tuple[float, float, float]:
        dlat = north_m / 111111.0
        lat_rad = math.radians(self.origin_lat_deg)
        dlon = east_m / (111111.0 * max(1e-6, abs(math.cos(lat_rad))))
        return self.origin_lat_deg + dlat, self.origin_lon_deg + dlon, self.origin_alt_m + up_m
