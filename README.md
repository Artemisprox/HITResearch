# HITResearch Sim Platform

面向“偏振增强的感知控制一体化安全飞行”的无界面数据平台骨架工程。

## 目标
- Isaac Sim 5.1 + Pegasus 纯后端批量仿真
- 森林/林缘场景双目 + IMU + 上视相机 + 真值轨迹采集
- GNSS 拒止条件下的太阳方向与天空偏振补全（libRadtran LUT）
- 统一数据存储、日志导出、可复现实验与参数化配置

## 快速开始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp configs/default.yaml configs/local.yaml
python scripts/run_batch.py --config configs/local.yaml --num-runs 2 --seed 42
```

## 目录
- `src/hitresearch_sim/core`：运行编排、随机性管理、坐标系绑定
- `src/hitresearch_sim/sensors`：双目/IMU/上视相机接口
- `src/hitresearch_sim/scenes`：森林场景与随机起飞点、轨迹生成
- `src/hitresearch_sim/polarization`：天空 mask、libRadtran LUT、偏振补全
- `src/hitresearch_sim/dataset`：统一数据写盘与 metadata
- `src/hitresearch_sim/interfaces`：健康度分析/模式切换/安全控制接口占位
- `scripts`：批处理入口

## 说明
当前版本先提供可运行的工程化框架与 mock 管线（便于你直接替换成 Isaac/Pegasus 实际 API）。
