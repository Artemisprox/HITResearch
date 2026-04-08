from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class HealthEstimate:
    score: float
    reason: str


class HealthEstimatorHook:
    def infer(self, _features: dict) -> HealthEstimate:
        return HealthEstimate(score=1.0, reason="placeholder")


class ModeSwitchHook:
    def decide(self, _health: HealthEstimate) -> str:
        return "normal"


class SafetyControlHook:
    def control(self, _mode: str, _state: dict) -> dict:
        return {"vx": 0.0, "vy": 0.0, "vz": 0.0, "yaw_rate": 0.0}
