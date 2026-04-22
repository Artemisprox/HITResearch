from pathlib import Path

import pytest

from hitresearch_sim.scenes.forest_scene import ForestScene


def test_mock_scene_load_returns_metadata() -> None:
    scene = ForestScene(map_name="forest_edge", backend="mock")
    meta = scene.load()
    assert meta["backend"] == "mock"
    assert meta["map_name"] == "forest_edge"


def test_isaac_scene_requires_isaac_modules_if_no_usd_path() -> None:
    scene = ForestScene(map_name="forest_edge", backend="isaac", usd_path=None)
    with pytest.raises(RuntimeError, match="Isaac Sim Python modules are unavailable"):
        scene.load()


def test_isaac_scene_requires_existing_usd_file(tmp_path: Path) -> None:
    scene = ForestScene(map_name="forest_edge", backend="isaac", usd_path=tmp_path / "missing.usd")
    with pytest.raises(FileNotFoundError):
        scene.load()
