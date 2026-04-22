from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class IsaacDroneRig:
    prim_path: str = "/World/Drone"

    def create(self, stage) -> dict[str, str]:
        from pxr import UsdGeom

        base = UsdGeom.Xform.Define(stage, self.prim_path)
        stereo_left = UsdGeom.Camera.Define(stage, f"{self.prim_path}/stereo_left")
        stereo_right = UsdGeom.Camera.Define(stage, f"{self.prim_path}/stereo_right")
        up_cam = UsdGeom.Camera.Define(stage, f"{self.prim_path}/upward_cam")
        imu = UsdGeom.Xform.Define(stage, f"{self.prim_path}/imu")

        UsdGeom.XformCommonAPI(stereo_left).SetTranslate((-0.08, 0.0, 0.02))
        UsdGeom.XformCommonAPI(stereo_right).SetTranslate((0.08, 0.0, 0.02))
        UsdGeom.XformCommonAPI(up_cam).SetTranslate((0.0, 0.0, 0.05))
        UsdGeom.XformCommonAPI(up_cam).SetRotate((180.0, 0.0, 0.0))
        UsdGeom.XformCommonAPI(imu).SetTranslate((0.0, 0.0, 0.0))
        _ = base

        return {
            "drone": self.prim_path,
            "stereo_left": f"{self.prim_path}/stereo_left",
            "stereo_right": f"{self.prim_path}/stereo_right",
            "upward_cam": f"{self.prim_path}/upward_cam",
            "imu": f"{self.prim_path}/imu",
        }

    def set_pose(self, stage, x: float, y: float, z: float, yaw_deg: float) -> None:
        from pxr import UsdGeom

        prim = UsdGeom.Xform.Get(stage, self.prim_path)
        UsdGeom.XformCommonAPI(prim).SetTranslate((float(x), float(y), float(z)))
        UsdGeom.XformCommonAPI(prim).SetRotate((0.0, 0.0, float(yaw_deg)))
