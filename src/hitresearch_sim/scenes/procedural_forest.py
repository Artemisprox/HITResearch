from __future__ import annotations

from math import cos, sin, tau

import numpy as np


def build_procedural_forest(
    stage,
    root_path: str,
    area_radius_m: float,
    tree_count: int,
    seed: int = 42,
) -> dict[str, int | float]:
    from pxr import Gf, UsdGeom

    rng = np.random.default_rng(seed)
    world = UsdGeom.Xform.Define(stage, root_path)

    ground = UsdGeom.Cube.Define(stage, f"{root_path}/Ground")
    ground.CreateSizeAttr(1.0)
    UsdGeom.XformCommonAPI(ground).SetScale((area_radius_m * 2.2, area_radius_m * 2.2, 0.2))
    UsdGeom.XformCommonAPI(ground).SetTranslate((0.0, 0.0, -0.1))

    for i in range(tree_count):
        theta = rng.random() * tau
        radius = area_radius_m * np.sqrt(rng.random())
        x = float(radius * cos(theta))
        y = float(radius * sin(theta))
        trunk_h = float(rng.uniform(6.0, 16.0))
        trunk_r = float(rng.uniform(0.15, 0.35))
        canopy_h = float(rng.uniform(3.0, 8.0))
        canopy_r = float(rng.uniform(1.2, 2.8))

        tree_root = f"{root_path}/Tree_{i:03d}"
        UsdGeom.Xform.Define(stage, tree_root)

        trunk = UsdGeom.Cylinder.Define(stage, f"{tree_root}/Trunk")
        trunk.CreateHeightAttr(trunk_h)
        trunk.CreateRadiusAttr(trunk_r)
        UsdGeom.XformCommonAPI(trunk).SetTranslate((x, y, trunk_h * 0.5))

        canopy = UsdGeom.Cone.Define(stage, f"{tree_root}/Canopy")
        canopy.CreateHeightAttr(canopy_h)
        canopy.CreateRadiusAttr(canopy_r)
        UsdGeom.XformCommonAPI(canopy).SetTranslate((x, y, trunk_h + canopy_h * 0.4))

    _ = world
    return {
        "tree_count": tree_count,
        "area_radius_m": float(area_radius_m),
    }
