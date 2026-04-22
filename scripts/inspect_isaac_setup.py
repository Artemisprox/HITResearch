#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hitresearch_sim.config.loader import load_config
from hitresearch_sim.scenes.forest_scene import ForestScene


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Isaac stage setup for forest + drone sensor mounts.")
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path")
    parser.add_argument("--gui", action="store_true", help="Open Isaac GUI while inspecting")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from omni.isaac.kit import SimulationApp
    except ImportError as exc:
        raise RuntimeError("Run this script in Isaac Sim Python environment.") from exc

    sim_app = SimulationApp({"headless": not args.gui})
    try:
        cfg = load_config(args.config)
        if cfg.scene.backend != "isaac":
            raise ValueError("Set scene.backend: isaac in config before running inspect script.")

        scene = ForestScene(
            map_name=cfg.scene.map_name,
            backend=cfg.scene.backend,
            usd_path=cfg.scene.usd_path,
            area_radius_m=cfg.scene.area_radius_m,
            tree_count=cfg.scene.tree_count,
            drone_prim_path=cfg.scene.drone_prim_path,
        )
        meta = scene.load()
        print("Scene meta:", meta)

        import omni.usd

        stage = omni.usd.get_context().get_stage()
        print("Top-level prims:")
        for prim in stage.GetPseudoRoot().GetChildren():
            print(" -", prim.GetPath())
    finally:
        sim_app.close()


if __name__ == "__main__":
    main()
