# 运行方法（Isaac + Pegasus 已安装环境）

## 1) 安装 Python 依赖
```bash
pip install -e .
```

## 2) 批量采集（无界面）
```bash
python scripts/run_batch.py --config configs/default.yaml --num-runs 5 --seed 123
```
每次执行会先清理目标 `run_xxx/` 输出目录，再写入新一轮帧数据，避免读取到历史残留帧。
当前默认是 `scene.backend: mock`，图像由程序纹理生成，颜色偏“示意化”用于验证链路，不代表真实渲染风格。

## 2.1) 调试阶段：启用 Isaac GUI 查看模块
```bash
python scripts/run_batch.py --config configs/default.yaml --gui --num-runs 1
```
说明：
- 该模式需要 Isaac Sim Python 环境（`omni.isaac.kit`）
- 适合先调试场景加载与模块状态，再切回无界面批量采集

若要专门检查场景与传感器挂载点：
```bash
python scripts/inspect_isaac_setup.py --config configs/default.yaml --gui
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
`ForestScene` 现在支持两种后端：
- `scene.backend: mock`（默认）
- `scene.backend: isaac`（会实际调用 Isaac Sim 的 `open_stage()` 载入 USD）

当 `scene.backend: isaac` 且 `scene.usd_path: null` 时，会创建程序化森林环境并自动搭建无人机传感器挂载点：
- `/World/Drone/stereo_left`
- `/World/Drone/stereo_right`
- `/World/Drone/upward_cam`
- `/World/Drone/imu`

示例配置（YAML）：
```yaml
scene:
  backend: isaac
  usd_path: /path/to/forest_scene.usd
sensors:
  provider: isaac
```

注意：
- 请在 Isaac Sim Python 环境中运行（能 import `omni.usd` 和 `omni.isaac.core`）
- 若配置了 `usd_path` 但文件不存在会直接报错
- 偏振模型实现细节见 `docs/POLARIZATION_MODEL.md`

其余模块仍是 mock 接口，建议逐步替换：
- 把 `sensors/*.py` 的 `capture()/sample()` 替换为 Pegasus 传感器 API
- `polarization/lut.py` 中 `build()` 替换为 libRadtran 真实调用与解析
