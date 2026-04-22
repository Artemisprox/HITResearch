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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    if args.seed is not None:
        cfg.run.seed = args.seed

    pipeline = SimulationPipeline(cfg)
    for run_idx in range(args.num_runs):
        out_dir = pipeline.run(run_idx)
        print(f"[run {run_idx}] dataset written to: {out_dir}")


if __name__ == "__main__":
    main()
