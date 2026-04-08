from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ForestScene:
    map_name: str

    def load(self) -> None:
        # TODO: replace with Isaac Sim USD loading
        return None
