# 运行方法（Isaac + Pegasus 已安装环境）

## 1) 安装 Python 依赖
```bash
pip install -e .
```

## 2) 批量采集（无界面）
```bash
python scripts/run_batch.py --config configs/default.yaml --num-runs 5 --seed 123
```

## 3) 输出结构
每次 run 会产生：
- `frame_xxxxxx/stereo_left.png`
- `frame_xxxxxx/stereo_right.png`
- `frame_xxxxxx/upward_rgb.png`
- `frame_xxxxxx/sky_mask.png`
- `frame_xxxxxx/dolp.npy`
- `frame_xxxxxx/aop.npy`
- `frame_xxxxxx/meta.json`
- `trajectory_gt.csv`

## 4) 接入 Isaac Sim / Pegasus
当前 `ForestScene` 与各 `Sensor` 是 mock 接口：
- 把 `scenes/forest_scene.py` 的 `load()` 替换为实际 USD 场景加载
- 把 `sensors/*.py` 的 `capture()/sample()` 替换为 Pegasus 传感器 API
- `polarization/lut.py` 中 `build()` 替换为 libRadtran 真实调用与解析
