from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_demo_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "demo_to_rviz_bag.py"
    spec = importlib.util.spec_from_file_location("demo_to_rviz_bag", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_yaw_to_quaternion_zero() -> None:
    module = _load_demo_module()
    qz, qw = module._yaw_to_quaternion(0.0)
    assert qz == 0.0
    assert qw == 1.0


def test_to_time_splits_sec_and_nanosec() -> None:
    module = _load_demo_module()

    class FakeTime:
        def __init__(self, sec: int, nanosec: int) -> None:
            self.sec = sec
            self.nanosec = nanosec

    stamp = module._to_time(1.25, FakeTime)
    assert stamp.sec == 1
    assert stamp.nanosec == 250_000_000
