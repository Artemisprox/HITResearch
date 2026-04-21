from pathlib import Path

from hitresearch_sim.config.loader import load_config


def test_load_config_coerces_output_root_to_path(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("run:\n  output_root: outputs\n", encoding="utf-8")

    cfg = load_config(cfg_path)

    assert isinstance(cfg.run.output_root, Path)
    assert cfg.run.output_root == Path("outputs")
