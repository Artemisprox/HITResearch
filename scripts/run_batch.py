#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from hitresearch_sim.config.loader import load_config
from hitresearch_sim.core.pipeline import SimulationPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run headless batch simulation data collection")
    parser.add_argument("--config", required=True, help="YAML config path")
    parser.add_argument("--num-runs", type=int, default=1, help="Batch run count")
    parser.add_argument("--seed", type=int, default=None, help="Override random seed")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Enable Isaac Sim GUI mode for scene debugging (requires Isaac environment)",
    )
    parser.add_argument(
        "--strict-isaac",
        action="store_true",
        help="Deprecated: Isaac mode is now strict by default.",
    )
    parser.add_argument(
        "--auto-close",
        action="store_true",
        help="In GUI mode, close app immediately when run finishes or errors (default keeps GUI open).",
    )
    return parser.parse_args()


def _hold_gui_open(sim_app) -> None:
    print("[info] GUI hold mode enabled. Press Ctrl+C to close Isaac Sim.")
    while True:
        try:
            sim_app.update()
            time.sleep(1.0 / 60.0)
        except KeyboardInterrupt:
            print("[info] Ctrl+C received, closing Isaac Sim.")
            break


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.seed is not None:
        cfg.run.seed = args.seed
    if cfg.scene.backend != "isaac" or cfg.sensors.provider != "isaac":
        raise ValueError(
            "This runner is now Isaac-only. Set scene.backend=isaac and sensors.provider=isaac."
        )

    sim_app = None
    need_isaac_app = cfg.scene.backend == "isaac"
    if need_isaac_app:
        SimulationApp = None
        try:
            from isaacsim.simulation_app import SimulationApp as _SimulationApp
            SimulationApp = _SimulationApp
        except ImportError:
            try:
                from omni.isaac.kit import SimulationApp as _SimulationApp  # backward-compat for older Isaac
                SimulationApp = _SimulationApp
            except ImportError as exc2:
                raise RuntimeError(
                    "Isaac simulation requires Isaac Sim Python environment (isaacsim/omni modules missing)."
                ) from exc2
        if SimulationApp is not None:
            if args.gui and not os.environ.get("DISPLAY"):
                print("[warn] DISPLAY is not set; GUI request will run headless. Set DISPLAY for windowed mode.")
            sim_app = SimulationApp({"headless": not args.gui})

    try:
        pipeline = SimulationPipeline(cfg)
        for run_idx in range(args.num_runs):
            out_dir = pipeline.run(run_idx)
            print(f"[run {run_idx}] dataset written to: {out_dir}")
    except Exception:
        if sim_app is not None and args.gui and not args.auto_close:
            print("[warn] Run failed, but keeping GUI open for debugging.")
            _hold_gui_open(sim_app)
        raise
    else:
        if sim_app is not None and args.gui and not args.auto_close:
            print("[info] Run complete; keeping GUI open for inspection.")
            _hold_gui_open(sim_app)
    finally:
        if sim_app is not None:
            sim_app.close()


if __name__ == "__main__":
    main()
