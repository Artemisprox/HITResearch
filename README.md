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

## 快速可视化 demo
```bash
python scripts/visualize_dataset.py \
  --dataset-dir outputs/forest_edge_baseline/run_000 \
  --frame-idx 10 \
  --save outputs/forest_edge_baseline/run_000/preview.png
```

## 输出
每个 run 输出一个 `dataset.csv`，包含：
- 轨迹/姿态真值（`t/x/y/z/yaw_deg`）
- IMU 真值（`imu_*`）
- 健康度、模式与控制占位字段
- 图像与偏振数组文件的相对路径（`*_path`）

## 目录
- `src/hitresearch_sim/core`：运行编排、随机性管理、坐标系绑定
- `src/hitresearch_sim/sensors`：双目/IMU/上视相机接口
- `src/hitresearch_sim/scenes`：森林场景与随机起飞点、轨迹生成
- `src/hitresearch_sim/polarization`：天空 mask、libRadtran LUT、偏振补全
- `src/hitresearch_sim/dataset`：统一数据写盘与 CSV 索引
- `src/hitresearch_sim/interfaces`：健康度分析/模式切换/安全控制接口占位
- `scripts`：批处理入口与可视化脚本

## 说明
当前版本提供可运行工程框架与 mock 管线（便于替换成 Isaac/Pegasus 实际 API）。
