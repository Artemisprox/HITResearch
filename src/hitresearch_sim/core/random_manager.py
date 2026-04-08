from __future__ import annotations

import random

import numpy as np


class RandomManager:
    def __init__(self, seed: int) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

    def uniform(self, low: float, high: float) -> float:
        return float(self.rng.uniform(low, high))

    def normal(self, mean: float, std: float) -> float:
        return float(self.rng.normal(mean, std))
