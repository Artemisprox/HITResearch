# HITResearch Sim Platform

面向“偏振增强的感知控制一体化安全飞行”的无界面数据平台骨架工程。

## 目标
- Isaac Sim 5.1 + Pegasus 纯后端批量仿真
- 森林/林缘场景双目 + IMU + 上视相机 + 真值轨迹采集
- GNSS 拒止条件下的太阳方向与天空偏振补全（libRadtran LUT）
- 统一 CSV 数据集、日志导出、可复现实验与参数化配置

## 快速开始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/run_batch.py --config configs/default.yaml --num-runs 2 --seed 42
```
`run_batch.py` 现在会在每次运行前清理对应 `run_xxx/` 目录，避免旧帧残留导致“看起来还是旧的黑图”。

> 若你看到图像“颜色不真实”，这是因为当前默认 `mock` 传感器是程序生成纹理（用于调试数据链路），不是真实渲染输出。

## 快速可视化 demo
```bash
python scripts/visualize_dataset.py \
  --dataset-dir outputs/forest_edge_baseline/run_000 \
  --frame-idx 10 \
  --save outputs/forest_edge_baseline/run_000/preview.png
```

## 导出 RViz 可演示的 rosbag2 demo
```bash
pip install -e '.[ros]'
python scripts/demo_to_rviz_bag.py --config configs/default.yaml --run-idx 0
```
该脚本会：
- 先跑一次 mock 仿真并生成 `dataset.csv`
- 再导出 `rviz_demo_bag/`（话题：`/hitresearch/path`、`/hitresearch/pose`、`/imu/data`）
- 可在 ROS 2 中 `ros2 bag play <bag_dir>`，然后用 RViz 订阅上述话题演示飞行轨迹

如遇 `Writer.__init__() missing ... 'version'` 或版本兼容问题，可显式指定：
```bash
python scripts/demo_to_rviz_bag.py --config configs/default.yaml --bag-version 9
```
若目标 bag 目录已存在，脚本默认自动切换为 `rviz_demo_bag_001`、`_002`…，避免直接报错；如需覆盖可加 `--overwrite`。

## 输出
每个 run 输出一个 `dataset.csv`，包含：
- 轨迹/姿态真值（`t/x/y/z/yaw_deg`）
- IMU 真值（`imu_*`）
- 健康度、模式与控制占位字段
- 图像与偏振数组文件的相对路径（`*_path`）

并会额外输出 `sensor_meta.json`（相机内参与传感器元数据）。

## 目录
- `src/hitresearch_sim/core`：运行编排、随机性管理、坐标系绑定
- `src/hitresearch_sim/sensors`：双目/IMU/上视相机接口
- `src/hitresearch_sim/scenes`：森林场景与随机起飞点、轨迹生成
- `src/hitresearch_sim/polarization`：天空 mask、libRadtran LUT、偏振补全
- `src/hitresearch_sim/dataset`：统一数据写盘与 CSV 索引
- `src/hitresearch_sim/interfaces`：健康度分析/模式切换/安全控制接口占位
- `scripts`：批处理入口与可视化脚本

## 说明
当前版本提供可运行工程框架与 mock 管线，并支持通过 `scene.backend: isaac` + `scene.usd_path` 直接加载森林 USD 场景。
当 `scene.backend: isaac` 且 `scene.usd_path` 为空时，会自动生成程序化森林（地面+树木）并创建带双目/上视/IMU 挂载点的无人机 prim，便于先做可视化调试。

## 调试阶段可视化（Isaac GUI）
```bash
python scripts/run_batch.py --config configs/default.yaml --gui --num-runs 1
```
用于先在可视化界面下检查场景加载和模块状态，确认后再切回无界面批量仿真。

要启用 Isaac 相机采集链路，请在配置中设置：
```yaml
scene:
  backend: isaac
sensors:
  provider: isaac
```
并可用 `python scripts/inspect_isaac_setup.py --config configs/default.yaml --gui` 先检查环境和挂载点。

偏振天空模型说明见：`docs/POLARIZATION_MODEL.md`。
