from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "run_batch.py"
    spec = importlib.util.spec_from_file_location("run_batch", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_batch_falls_back_to_mock_when_isaac_missing(monkeypatch) -> None:
    module = _load_module()
    args = SimpleNamespace(config="unused.yaml", num_runs=1, seed=None, gui=False, strict_isaac=False)
    cfg = SimpleNamespace(
        scene=SimpleNamespace(backend="isaac"),
        sensors=SimpleNamespace(provider="isaac"),
        run=SimpleNamespace(seed=42),
    )

    class DummyPipeline:
        def __init__(self, config):
            self.config = config

        def run(self, run_idx: int):
            _ = run_idx
            return Path("outputs/mock/run_000")

    monkeypatch.setattr(module, "parse_args", lambda: args)
    monkeypatch.setattr(module, "load_config", lambda _path: cfg)
    monkeypatch.setattr(module, "SimulationPipeline", DummyPipeline)
    module.main()
    assert cfg.scene.backend == "mock"
    assert cfg.sensors.provider == "mock"
