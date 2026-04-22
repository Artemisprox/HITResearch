from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import shutil

from hitresearch_sim.config.schema import AppConfig
from hitresearch_sim.dataset.writer import DatasetWriter
from hitresearch_sim.interfaces.hooks import HealthEstimatorHook, ModeSwitchHook, SafetyControlHook
from hitresearch_sim.polarization.compositor import PolarizationCompositor
from hitresearch_sim.polarization.lut import LibRadtranLUTBuilder
from hitresearch_sim.polarization.sky_mask import SkyMaskExtractor
from hitresearch_sim.scenes.forest_scene import ForestScene
from hitresearch_sim.scenes.trajectory import TrajectoryGenerator
from hitresearch_sim.sensors.imu import ImuSensor
from hitresearch_sim.sensors.stereo import StereoSensor
from hitresearch_sim.sensors.upward_camera import UpwardCamera


class SimulationPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.scene = ForestScene(config.scene.map_name)
        self.traj = TrajectoryGenerator(
            radius_m=config.scene.area_radius_m,
            min_alt_m=config.scene.min_altitude_m,
            max_alt_m=config.scene.max_altitude_m,
        )
        self.stereo = StereoSensor(config.sensors.stereo_width, config.sensors.stereo_height)
        self.imu = ImuSensor()
        self.up_cam = UpwardCamera(config.sensors.up_width, config.sensors.up_height)
        self.masker = SkyMaskExtractor()
        self.lut_builder = LibRadtranLUTBuilder(config.polarization.lib_radtran_bin)
        self.compositor = PolarizationCompositor()
        self.health = HealthEstimatorHook()
        self.mode_switch = ModeSwitchHook()
        self.safety = SafetyControlHook()

    def run(self, run_idx: int) -> Path:
        out_dir = self.config.run.output_root / self.config.run.scenario_id / f"run_{run_idx:03d}"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        writer = DatasetWriter(out_dir)

        self.scene.load()
        points = self.traj.circular(self.config.run.duration_s, self.config.run.dt_s)
        lut = self.lut_builder.build(solar_zenith_deg=40.0, solar_azimuth_deg=140.0, out_dir=out_dir)

        for i, p in enumerate(points):
            left, right = self.stereo.capture()
            upward = self.up_cam.capture()
            imu = self.imu.sample()
            sky_mask = self.masker.extract(upward)
            pol = self.compositor.compose(upward, sky_mask, lut)

            health = self.health.infer(pol)
            mode = self.mode_switch.decide(health)
            ctrl = self.safety.control(mode, {"x": p.x, "y": p.y, "z": p.z})

            writer.write_frame(
                i,
                {
                    "stereo_left": left,
                    "stereo_right": right,
                    **pol,
                    "meta": {
                        "t": p.t,
                        "x": p.x,
                        "y": p.y,
                        "z": p.z,
                        "yaw_deg": p.yaw_deg,
                        "imu": asdict(imu),
                        "health": asdict(health),
                        "mode": mode,
                        "control": ctrl,
                    },
                },
            )
        writer.finalize()
        return out_dir
