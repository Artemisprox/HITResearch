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
from hitresearch_sim.sensors.imu import ImuSample, ImuSensor
from hitresearch_sim.sensors.stereo import StereoSensor
from hitresearch_sim.sensors.upward_camera import UpwardCamera


class SimulationPipeline:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.scene = ForestScene(
            config.scene.map_name,
            backend=config.scene.backend,
            usd_path=config.scene.usd_path,
            area_radius_m=config.scene.area_radius_m,
            tree_count=config.scene.tree_count,
            drone_prim_path=config.scene.drone_prim_path,
        )
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

        scene_meta = self.scene.load()
        isaac_stage = None
        isaac_drone = None
        if scene_meta.get("backend") == "isaac":
            try:
                import omni.usd
                from hitresearch_sim.platforms.isaac_drone import IsaacDroneRig
            except ImportError:
                isaac_stage = None
            else:
                isaac_stage = omni.usd.get_context().get_stage()
                isaac_drone = IsaacDroneRig(prim_path=self.config.scene.drone_prim_path)
        isaac_bridge = None
        if scene_meta.get("backend") == "isaac" and self.config.sensors.provider == "isaac":
            from hitresearch_sim.sensors.isaac_bridge import IsaacSensorBridge

            base = self.config.scene.drone_prim_path
            isaac_bridge = IsaacSensorBridge(
                stereo_left_prim=f"{base}/stereo_left",
                stereo_right_prim=f"{base}/stereo_right",
                upward_prim=f"{base}/upward_cam",
                imu_prim=f"{base}/imu",
                stereo_width=self.config.sensors.stereo_width,
                stereo_height=self.config.sensors.stereo_height,
                upward_width=self.config.sensors.up_width,
                upward_height=self.config.sensors.up_height,
            )
            sensor_meta = isaac_bridge.intrinsics()
        else:
            sensor_meta = {
                "stereo": self.stereo.intrinsics(),
                "upward": self.up_cam.intrinsics(),
            }

        writer = DatasetWriter(out_dir, sensor_meta=sensor_meta)
        points = self.traj.circular(self.config.run.duration_s, self.config.run.dt_s)
        lut = self.lut_builder.build(
            solar_zenith_deg=self.config.polarization.solar_zenith_deg,
            solar_azimuth_deg=self.config.polarization.solar_azimuth_deg,
            out_dir=out_dir,
        )

        for i, p in enumerate(points):
            if isaac_stage is not None and isaac_drone is not None:
                isaac_drone.set_pose(isaac_stage, p.x, p.y, p.z, p.yaw_deg)
            if isaac_bridge is not None:
                try:
                    import omni.kit.app
                except ImportError:
                    pass
                else:
                    omni.kit.app.get_app().update()
                left, right = isaac_bridge.capture_stereo()
                upward = isaac_bridge.capture_upward()
                imu = ImuSample(**isaac_bridge.sample_imu())
            else:
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
