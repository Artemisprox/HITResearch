from pathlib import Path

from hitresearch_sim.config.loader import load_config


def test_load_config_coerces_output_root_to_path(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "run:\n  output_root: outputs\nscene:\n  usd_path: /tmp/forest.usd\nsensors:\n  provider: isaac\npolarization:\n  solar_zenith_deg: 35.0\n  solar_azimuth_deg: 120.0\n",
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)

    assert isinstance(cfg.run.output_root, Path)
    assert cfg.run.output_root == Path("outputs")
    assert isinstance(cfg.scene.usd_path, Path)
    assert cfg.scene.usd_path == Path("/tmp/forest.usd")
    assert cfg.sensors.provider == "isaac"
    assert cfg.polarization.solar_zenith_deg == 35.0
    assert cfg.polarization.solar_azimuth_deg == 120.0
