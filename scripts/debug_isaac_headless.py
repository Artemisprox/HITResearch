#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug Isaac headless startup and sensor capture pipeline.")
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path")
    parser.add_argument(
        "--report",
        default="outputs/debug/isaac_headless_report.json",
        help="Path to write JSON debug report",
    )
    return parser.parse_args()


def _flush_report(report_path: Path, report: dict[str, Any]) -> None:
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _step(report: dict[str, Any], report_path: Path, name: str, status: str, detail: str, **extra: Any) -> None:
    report["steps"].append({"name": name, "status": status, "detail": detail, **extra})
    _flush_report(report_path, report)
    print(f"[{status}] {name}: {detail}", flush=True)


def main() -> None:
    args = parse_args()
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config": args.config,
        "display": os.environ.get("DISPLAY"),
        "steps": [],
        "ok": False,
    }
    _flush_report(report_path, report)

    sim_app = None
    bridge = None
    try:
        from hitresearch_sim.config.loader import load_config
        from hitresearch_sim.scenes.forest_scene import ForestScene
        from hitresearch_sim.sensors.isaac_bridge import IsaacSensorBridge

        cfg = load_config(args.config)
        _step(
            report,
            report_path,
            "load_config",
            "ok",
            "Config loaded",
            scene_backend=cfg.scene.backend,
            sensor_provider=cfg.sensors.provider,
        )
        if cfg.scene.backend != "isaac" or cfg.sensors.provider != "isaac":
            raise ValueError("Debug script requires scene.backend=isaac and sensors.provider=isaac")

        from isaacsim.simulation_app import SimulationApp

        sim_app = SimulationApp({"headless": True})
        _step(report, report_path, "simulation_app", "ok", "SimulationApp started in headless mode")

        scene = ForestScene(
            map_name=cfg.scene.map_name,
            backend=cfg.scene.backend,
            usd_path=cfg.scene.usd_path,
            area_radius_m=cfg.scene.area_radius_m,
            tree_count=cfg.scene.tree_count,
            drone_prim_path=cfg.scene.drone_prim_path,
        )
        scene_meta = scene.load()
        _step(report, report_path, "scene_load", "ok", "Scene loaded", scene_meta=scene_meta)

        import omni.usd

        stage = omni.usd.get_context().get_stage()
        if stage is None:
            raise RuntimeError("USD stage is None after scene load")
        base = cfg.scene.drone_prim_path
        expected_prims = [
            f"{base}/stereo_left",
            f"{base}/stereo_right",
            f"{base}/upward_cam",
            f"{base}/imu",
        ]
        missing = [p for p in expected_prims if not stage.GetPrimAtPath(p).IsValid()]
        if missing:
            raise RuntimeError(f"Missing sensor prims: {missing}")
        _step(report, report_path, "prim_check", "ok", "All expected sensor prims exist", prims=expected_prims)

        from pxr import UsdGeom

        camera_checks = {}
        for p in expected_prims[:-1]:
            prim = stage.GetPrimAtPath(p)
            camera_checks[p] = {
                "type_name": prim.GetTypeName(),
                "is_camera": prim.IsA(UsdGeom.Camera),
            }
        _step(report, report_path, "camera_schema", "ok", "Checked camera prim schemas", cameras=camera_checks)

        bridge = IsaacSensorBridge(
            stereo_left_prim=f"{base}/stereo_left",
            stereo_right_prim=f"{base}/stereo_right",
            upward_prim=f"{base}/upward_cam",
            imu_prim=f"{base}/imu",
            stereo_width=cfg.sensors.stereo_width,
            stereo_height=cfg.sensors.stereo_height,
            upward_width=cfg.sensors.up_width,
            upward_height=cfg.sensors.up_height,
        )

        bridge.warmup()
        _step(report, report_path, "bridge_warmup", "ok", "Isaac sensor bridge warmup succeeded")

        left, right = bridge.capture_stereo()
        upward = bridge.capture_upward()
        imu = bridge.sample_imu()
        _step(
            report,
            report_path,
            "capture_once",
            "ok",
            "Captured stereo/upward/imu once",
            left_shape=list(left.shape),
            right_shape=list(right.shape),
            upward_shape=list(upward.shape),
            left_mean=float(left.mean()),
            right_mean=float(right.mean()),
            upward_mean=float(upward.mean()),
            imu=imu,
        )

        report["ok"] = True
    except Exception as exc:
        tb = traceback.format_exc()
        bridge_diag = bridge.diagnostics() if bridge is not None else None
        _step(report, report_path, "exception", "error", str(exc), traceback=tb, bridge=bridge_diag)
        report["ok"] = False
    finally:
        if sim_app is not None:
            sim_app.close()
            _step(report, report_path, "simulation_app_close", "ok", "SimulationApp closed")
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        _flush_report(report_path, report)
        print(f"Debug report written to: {report_path}", flush=True)

    if not report["ok"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
