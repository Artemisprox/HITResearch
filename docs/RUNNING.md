# 运行方法（Isaac + Pegasus 已安装环境）

## 1) 安装 Python 依赖
```bash
pip install -e .
```

## 2) 批量采集（无界面）
```bash
python scripts/run_batch.py --config configs/default.yaml --num-runs 5 --seed 123
```

## 3) 输出结构（CSV）
每个 `run_xxx` 目录包含：
- `dataset.csv`（统一索引与真值主表）
- `frame_xxxxxx/stereo_left.png`
- `frame_xxxxxx/stereo_right.png`
- `frame_xxxxxx/upward_rgb.png`
- `frame_xxxxxx/sky_mask.png`
- `frame_xxxxxx/dolp.npy`
- `frame_xxxxxx/aop.npy`

> `dataset.csv` 每一行对应一个时间步，记录状态真值 + 传感器文件相对路径。

## 4) 快速可视化 demo
```bash
python scripts/visualize_dataset.py \
  --dataset-dir outputs/forest_edge_baseline/run_000 \
  --frame-idx 10 \
  --save outputs/forest_edge_baseline/run_000/preview.png
```

## 5) 导出 RViz 可演示的 rosbag2
```bash
pip install -e '.[ros]'
python scripts/demo_to_rviz_bag.py --config configs/default.yaml --run-idx 0
```
默认会在对应 run 目录下生成 `rviz_demo_bag/`，包含：
- `/hitresearch/path` (`nav_msgs/msg/Path`)
- `/hitresearch/pose` (`geometry_msgs/msg/PoseStamped`)
- `/imu/data` (`sensor_msgs/msg/Imu`)

在 ROS 2 环境中可执行：
```bash
ros2 bag play outputs/<scenario_id>/run_000/rviz_demo_bag
```
再打开 RViz 订阅上述话题进行轨迹与姿态演示。

若本机 `rosbags` 版本要求显式传入 `Writer` 的 `version` 参数，可用：
```bash
python scripts/demo_to_rviz_bag.py --config configs/default.yaml --bag-version 9
```
如果 `rviz_demo_bag/` 已存在，默认会自动创建 `rviz_demo_bag_001` 等新目录；要覆盖原目录请加 `--overwrite`。

## 6) 接入 Isaac Sim / Pegasus
当前 `ForestScene` 与各 `Sensor` 是 mock 接口：
- 把 `scenes/forest_scene.py` 的 `load()` 替换为实际 USD 场景加载
- 把 `sensors/*.py` 的 `capture()/sample()` 替换为 Pegasus 传感器 API
- `polarization/lut.py` 中 `build()` 替换为 libRadtran 真实调用与解析
