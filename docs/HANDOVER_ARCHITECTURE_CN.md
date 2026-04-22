# HITResearch Sim 接手文档（架构 + 文件职责）

> 目标：让你**快速接手**当前工程，明确“每个文件做什么、数据怎么流动、出现问题先看哪里”。

## 1. 先建立全局认知

当前项目是一条 **Isaac-only 数据生成流水线**：

1. `scripts/run_batch.py` 读取配置，启动 Isaac `SimulationApp`。
2. `SimulationPipeline` 负责完整帧循环：场景加载 → 轨迹驱动无人机 → 采集传感器 → 偏振估计 → 写盘。
3. `DatasetWriter` 落盘成统一目录（`dataset.csv` + 每帧图片/数组 + `sensor_meta.json`）。
4. 额外脚本做可视化与 RViz bag 导出。

一句话：**入口脚本负责进程和模式，pipeline 负责时序编排，子模块负责“各自一件事”。**

---

## 2. 运行时主链路（按调用顺序）

### 2.1 入口层（CLI）
- `scripts/run_batch.py`
  - 参数解析：`--config --num-runs --seed --gui`。
  - 严格校验配置必须是 `scene.backend=isaac` 且 `sensors.provider=isaac`。
  - 初始化 Isaac `SimulationApp`（可 headless / GUI）。
  - 循环调用 `SimulationPipeline.run(run_idx)`。

### 2.2 编排层（核心）
- `src/hitresearch_sim/core/pipeline.py`
  - 初始化：场景、轨迹、传感器、偏振模块、控制接口占位。
  - `run()` 时做：
    - 清理旧输出目录（避免历史脏数据）。
    - `ForestScene.load()` 场景准备。
    - 构造 `IsaacSensorBridge` 并 `warmup()`。
    - 生成轨迹点，循环每一帧：
      - 设置无人机位姿；
      - `capture_stereo()/capture_upward()/sample_imu()`；
      - `SkyMaskExtractor` + `PolarizationCompositor` 生成 `sky_mask/dolp/aop`；
      - 调用 health/mode/control 占位 hook；
      - `DatasetWriter.write_frame()` 落盘。
    - `finalize()` 写 `dataset.csv`。

### 2.3 场景层
- `src/hitresearch_sim/scenes/forest_scene.py`
  - `backend=isaac`：
    - 有 `usd_path`：打开外部 USD。
    - 无 `usd_path`：新建 stage + 程序化森林。
  - 挂载无人机 prim 与相机/IMU 子 prim。

- `src/hitresearch_sim/scenes/procedural_forest.py`
  - 在 USD stage 中生成地面、树干、树冠几何体。

- `src/hitresearch_sim/platforms/isaac_drone.py`
  - 定义无人机 prim 结构：
    - `/stereo_left`, `/stereo_right`, `/upward_cam`, `/imu`
  - 提供 `set_pose()` 每帧更新机体位姿。

### 2.4 传感器层
- `src/hitresearch_sim/sensors/isaac_bridge.py`
  - 用 Replicator annotator 拉取 RGB 帧。
  - `warmup()` 做 app update + 首帧有效性检查。
  - `sample_imu()` 优先 Isaac IMU API，不可用时给 fallback 值并打印 warn。
  - 提供 `intrinsics()` 输出相机元数据。

- `src/hitresearch_sim/sensors/stereo.py`
- `src/hitresearch_sim/sensors/upward_camera.py`
- `src/hitresearch_sim/sensors/imu.py`
  - 以上是 mock/占位传感器实现，便于测试或离线验证。
  - 注意：当前 `run_batch.py` 主流程已要求 Isaac-only，不再作为批量入口默认路径。

### 2.5 偏振层
- `src/hitresearch_sim/polarization/lut.py`
  - 现阶段使用 Rayleigh 近似生成 DoLP/AoP LUT。
- `src/hitresearch_sim/polarization/sky_mask.py`
  - 基于颜色阈值的天空掩码。
- `src/hitresearch_sim/polarization/compositor.py`
  - 将上视图像坐标映射到 LUT，生成逐像素 `dolp/aop`。

### 2.6 数据层
- `src/hitresearch_sim/dataset/writer.py`
  - 每帧写：`stereo_left/right`, `upward_rgb`, `sky_mask`, `dolp`, `aop`。
  - 运行级写：`dataset.csv` + `sensor_meta.json`。

### 2.7 配置层
- `configs/default.yaml`：默认实验参数。
- `src/hitresearch_sim/config/schema.py`：配置 dataclass 结构。
- `src/hitresearch_sim/config/loader.py`：YAML 合并 + `Path` 类型转换。

---

## 3. 文件逐个说明（你关心的“每个文件做什么”）

> 按仓库现有文件列出，便于直接对照接手。

## 根目录
- `README.md`：项目入口说明、快速运行命令、模块目录导览。
- `pyproject.toml`：包依赖与可选 extras（如 rosbag 导出依赖）。

## 配置
- `configs/default.yaml`：默认 run/sensors/scene/geo/polarization 参数。

## 文档
- `docs/RUNNING.md`：运行手册（Isaac 环境、GUI/headless、输出说明）。
- `docs/POLARIZATION_MODEL.md`：偏振模型（Rayleigh 近似）说明。
- `docs/HANDOVER_ARCHITECTURE_CN.md`：本接手文档。

## 脚本（scripts）
- `scripts/run_batch.py`：批量采集主入口（强约束 Isaac-only）。
- `scripts/inspect_isaac_setup.py`：检查 Isaac 环境 + 预期 prim 挂载结构。
- `scripts/demo_to_rviz_bag.py`：将 dataset 导出为 rosbag2（RViz 演示）。
- `scripts/visualize_dataset.py`：快速可视化轨迹、姿态、图像与 DoLP。

## 核心包（src/hitresearch_sim）
- `__init__.py`：包标识。

### core
- `core/pipeline.py`：系统总编排器（真正的数据生产主循环）。
- `core/geo.py`：ENU 到 LLA 的简化转换。
- `core/random_manager.py`：统一随机数管理。

### config
- `config/schema.py`：配置 dataclass 定义。
- `config/loader.py`：配置加载、递归 merge、类型转换。

### scenes
- `scenes/forest_scene.py`：场景后端选择与 stage 构建。
- `scenes/procedural_forest.py`：程序化森林几何生成。
- `scenes/trajectory.py`：轨迹采样（圆轨迹 + 航向）。

### platforms
- `platforms/__init__.py`：平台包标识。
- `platforms/isaac_drone.py`：无人机 prim 结构创建与位姿设置。

### sensors
- `sensors/isaac_bridge.py`：Isaac 传感器桥接（相机 + IMU + 内参）。
- `sensors/stereo.py`：mock 双目。
- `sensors/upward_camera.py`：mock 上视相机。
- `sensors/imu.py`：mock IMU 数据结构与采样。

### polarization
- `polarization/lut.py`：DoLP/AoP LUT 生成。
- `polarization/sky_mask.py`：天空掩码提取。
- `polarization/compositor.py`：LUT 合成到图像坐标。

### dataset
- `dataset/writer.py`：帧文件与 CSV 索引落盘。

### interfaces
- `interfaces/hooks.py`：健康评估/模式切换/控制占位接口。

## 测试（tests）
- `tests/test_run_batch_script.py`：入口脚本在 Isaac 缺失时是否按预期失败。
- `tests/test_isaac_bridge.py`：Isaac bridge 的关键行为单测。
- `tests/test_forest_scene.py`：场景加载行为单测。
- `tests/test_config_loader.py`：配置加载与 Path 转换单测。
- `tests/test_mock_sensor_outputs.py`：mock 传感器输出性质单测。
- `tests/test_polarization_model.py`：偏振模块数值与输出形态单测。
- `tests/test_inspect_script.py`：inspect 脚本行为单测。
- `tests/test_demo_to_rviz_bag.py`：bag 导出工具函数与目录策略单测。

---

## 4. 数据与目录约定（接手时最常用）

单次 run 输出：

- `outputs/<scenario_id>/run_xxx/dataset.csv`
- `outputs/<scenario_id>/run_xxx/sensor_meta.json`
- `outputs/<scenario_id>/run_xxx/frame_000000/...`

每行 CSV 对应一个时间步，存真值字段 + 文件相对路径；图像/数组实体在每帧目录。

---

## 5. 你接手后建议的学习路径（最快上手）

1. 先读 `scripts/run_batch.py` + `core/pipeline.py`（抓主流程）。
2. 再读 `forest_scene.py` + `isaac_bridge.py`（抓 Isaac 场景和采集）。
3. 再读 `dataset/writer.py` + `configs/default.yaml`（抓输入输出契约）。
4. 最后读 `polarization/*` + `interfaces/hooks.py`（抓可替换算法层）。

---

## 6. 常见排查入口（按症状）

- **跑不起来 / Isaac 模块报错**：先看 `scripts/run_batch.py`、`scripts/inspect_isaac_setup.py`。
- **相机帧空或异常**：看 `sensors/isaac_bridge.py` 的 `warmup()` 与 `_to_bgr()`。
- **轨迹不对**：看 `scenes/trajectory.py` 与 `platforms/isaac_drone.py:set_pose()`。
- **输出目录有旧数据疑问**：看 `core/pipeline.py` 开头的目录清理逻辑。
- **偏振图不合理**：看 `polarization/sky_mask.py` 阈值和 `polarization/compositor.py` 映射关系。

---

## 7. 当前可演进点（后续你可直接改）

1. `isaac_bridge.py` 的 IMU fallback 改成稳定的 Isaac 原生 IMU 读取链路。
2. `polarization/lut.py` 从 Rayleigh 近似升级为真实 libRadtran 调用与解析。
3. `interfaces/hooks.py` 接入真实健康评估与控制策略，替换占位返回。
4. `trajectory.py` 扩展多段任务轨迹（爬升/巡航/绕障）并配套单测。

