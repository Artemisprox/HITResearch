from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ForestScene:
    map_name: str
    backend: str = "mock"
    usd_path: Path | None = None

    def load(self) -> dict[str, Any]:
        if self.backend == "mock":
            return {"backend": "mock", "map_name": self.map_name}
        if self.backend != "isaac":
            raise ValueError(f"Unsupported scene backend: {self.backend}")
        return self._load_isaac_scene()

    def _load_isaac_scene(self) -> dict[str, Any]:
        if self.usd_path is None:
            raise ValueError("scene.usd_path is required when scene.backend == 'isaac'")
        if not self.usd_path.exists():
            raise FileNotFoundError(f"Scene USD file not found: {self.usd_path}")

        try:
            import omni.usd
            from omni.isaac.core.utils.stage import open_stage
        except ImportError as exc:
            raise RuntimeError(
                "Isaac Sim Python modules are unavailable. Start with Isaac Sim Python env, "
                "or switch scene.backend to 'mock'."
            ) from exc

        ok = open_stage(str(self.usd_path))
        if not ok:
            raise RuntimeError(f"Failed to open USD stage: {self.usd_path}")

        stage = omni.usd.get_context().get_stage()
        if stage is None:
            raise RuntimeError(f"USD stage context is empty after loading: {self.usd_path}")

        return {
            "backend": "isaac",
            "map_name": self.map_name,
            "usd_path": str(self.usd_path),
            "stage_id": stage.GetRootLayer().identifier,
        }
