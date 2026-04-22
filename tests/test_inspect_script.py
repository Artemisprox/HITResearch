from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "inspect_isaac_setup.py"
    spec = importlib.util.spec_from_file_location("inspect_isaac_setup", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_main_does_not_raise_when_isaac_missing(monkeypatch) -> None:
    module = _load_module()
    args = SimpleNamespace(config="unused.yaml", gui=False, strict=False)
    cfg = SimpleNamespace(
        scene=SimpleNamespace(backend="isaac", usd_path=None, drone_prim_path="/World/Drone"),
        sensors=SimpleNamespace(provider="isaac"),
    )
    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module, "load_config", lambda _path: cfg)
    module.main()
