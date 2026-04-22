from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import yaml

from .schema import AppConfig, GeoConfig, PolarizationConfig, RunConfig, SceneConfig, SensorConfig


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _merge(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path: str | Path) -> AppConfig:
    cfg = AppConfig()
    raw = asdict(cfg)
    with Path(path).open("r", encoding="utf-8") as f:
        user_cfg = yaml.safe_load(f) or {}
    merged = _merge(raw, user_cfg)
    run_cfg = merged["run"]
    run_cfg["output_root"] = Path(run_cfg["output_root"])
    scene_cfg = merged["scene"]
    if scene_cfg.get("usd_path") is not None:
        scene_cfg["usd_path"] = Path(scene_cfg["usd_path"])

    return AppConfig(
        run=RunConfig(**run_cfg),
        sensors=SensorConfig(**merged["sensors"]),
        scene=SceneConfig(**scene_cfg),
        geo=GeoConfig(**merged["geo"]),
        polarization=PolarizationConfig(**merged["polarization"]),
    )
