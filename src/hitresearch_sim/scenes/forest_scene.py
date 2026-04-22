from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ForestScene:
    map_name: str
    backend: str = "mock"
    usd_path: Path | None = None
    area_radius_m: float = 100.0
    tree_count: int = 80
    drone_prim_path: str = "/World/Drone"

    def load(self) -> dict[str, Any]:
        if self.backend == "mock":
            return {"backend": "mock", "map_name": self.map_name}
        if self.backend != "isaac":
            raise ValueError(f"Unsupported scene backend: {self.backend}")
        return self._load_isaac_scene()

    def _load_isaac_scene(self) -> dict[str, Any]:
        if self.usd_path is not None and not self.usd_path.exists():
            raise FileNotFoundError(f"Scene USD file not found: {self.usd_path}")

        try:
            import omni.usd
            from omni.isaac.core.utils.stage import open_stage
        except ImportError as exc:
            raise RuntimeError(
                "Isaac Sim Python modules are unavailable. Start with Isaac Sim Python env, "
                "or switch scene.backend to 'mock'."
            ) from exc

        usd_ctx = omni.usd.get_context()
        loaded_from_file = False
        if self.usd_path is not None:
            ok = open_stage(str(self.usd_path))
            if not ok:
                raise RuntimeError(f"Failed to open USD stage: {self.usd_path}")
            loaded_from_file = True
        else:
            usd_ctx.new_stage()

        stage = usd_ctx.get_stage()
        if stage is None:
            raise RuntimeError("USD stage context is empty after scene setup")

        from hitresearch_sim.platforms.isaac_drone import IsaacDroneRig
        from hitresearch_sim.scenes.procedural_forest import build_procedural_forest

        forest_meta: dict[str, Any] = {}
        if not loaded_from_file:
            forest_meta = build_procedural_forest(
                stage=stage,
                root_path="/World/Forest",
                area_radius_m=self.area_radius_m,
                tree_count=self.tree_count,
            )
        drone_meta = IsaacDroneRig(prim_path=self.drone_prim_path).create(stage)

        return {
            "backend": "isaac",
            "map_name": self.map_name,
            "usd_path": str(self.usd_path) if self.usd_path is not None else None,
            "stage_id": stage.GetRootLayer().identifier,
            "forest": forest_meta,
            "drone": drone_meta,
        }
