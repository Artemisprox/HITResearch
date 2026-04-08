from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class SensorConfig:
    stereo_width: int = 1280
    stereo_height: int = 720
    up_width: int = 1024
    up_height: int = 1024
    imu_hz: int = 200
    cam_hz: int = 30


@dataclass(slots=True)
class SceneConfig:
    map_name: str = "forest_edge"
    area_radius_m: float = 200.0
    min_altitude_m: float = 20.0
    max_altitude_m: float = 80.0


@dataclass(slots=True)
class GeoConfig:
    origin_lat_deg: float = 30.0
    origin_lon_deg: float = 114.0
    origin_alt_m: float = 50.0


@dataclass(slots=True)
class PolarizationConfig:
    lib_radtran_bin: str = "/opt/libRadtran/bin/uvspec"
    solar_wavelength_nm: int = 550
    dolp_clip: float = 1.0


@dataclass(slots=True)
class RunConfig:
    output_root: Path = Path("outputs")
    duration_s: float = 60.0
    dt_s: float = 1.0 / 30.0
    seed: int = 42
    scenario_id: str = "default"


@dataclass(slots=True)
class AppConfig:
    run: RunConfig = field(default_factory=RunConfig)
    sensors: SensorConfig = field(default_factory=SensorConfig)
    scene: SceneConfig = field(default_factory=SceneConfig)
    geo: GeoConfig = field(default_factory=GeoConfig)
    polarization: PolarizationConfig = field(default_factory=PolarizationConfig)
