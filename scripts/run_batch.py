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
        help="Fail immediately if Isaac backend is requested but omni modules are unavailable",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.seed is not None:
        cfg.run.seed = args.seed

    sim_app = None
    need_isaac_app = cfg.scene.backend == "isaac"
    if need_isaac_app:
        try:
            from omni.isaac.kit import SimulationApp
        except ImportError as exc:
            if args.strict_isaac:
                raise RuntimeError(
                    "Isaac simulation requires Isaac Sim Python environment (omni.isaac.kit is missing)."
                ) from exc
            print("[warn] omni.isaac.kit is missing; fallback to mock backend for this run.")
            cfg.scene.backend = "mock"
            cfg.sensors.provider = "mock"
            need_isaac_app = False
        else:
            sim_app = SimulationApp({"headless": not args.gui})

    try:
        pipeline = SimulationPipeline(cfg)
        for run_idx in range(args.num_runs):
            out_dir = pipeline.run(run_idx)
            print(f"[run {run_idx}] dataset written to: {out_dir}")
    finally:
        if sim_app is not None:
            sim_app.close()


if __name__ == "__main__":
    main()
