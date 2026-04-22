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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with non-zero error when Isaac Python modules are unavailable",
    )
    return parser.parse_args()


def _print_expected_layout(cfg) -> None:
    base = cfg.scene.drone_prim_path
    print("Expected sensor prims:")
    print(f" - {base}/stereo_left")
    print(f" - {base}/stereo_right")
    print(f" - {base}/upward_cam")
    print(f" - {base}/imu")


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    try:
        from omni.isaac.kit import SimulationApp
    except ImportError as exc:
        print("[warn] Isaac module 'omni.isaac.kit' not found in current Python environment.")
        print("Current config summary:")
        print(f" - scene.backend: {cfg.scene.backend}")
        print(f" - scene.usd_path: {cfg.scene.usd_path}")
        print(f" - sensors.provider: {cfg.sensors.provider}")
        _print_expected_layout(cfg)
        print("\nTo run real Isaac inspection, execute this script inside Isaac Sim Python environment.")
        if args.strict:
            raise RuntimeError("Run this script in Isaac Sim Python environment.") from exc
        return

    sim_app = SimulationApp({"headless": not args.gui})
    try:
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
        _print_expected_layout(cfg)
    finally:
        sim_app.close()


if __name__ == "__main__":
    main()
