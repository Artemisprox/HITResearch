#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one mock simulation and export flight trajectory/IMU into a ROS2 bag for RViz."
    )
    parser.add_argument("--config", default="configs/default.yaml", help="YAML config path")
    parser.add_argument("--run-idx", type=int, default=0, help="Run index used for output folder naming")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="Use an existing dataset run directory (if set, no simulation will be executed)",
    )
    parser.add_argument(
        "--bag-dir",
        type=Path,
        default=None,
        help="Output rosbag2 directory (default: <run_dir>/rviz_demo_bag)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing bag directory if it already exists",
    )
    return parser.parse_args()


def _yaw_to_quaternion(yaw_deg: float) -> tuple[float, float]:
    yaw = math.radians(float(yaw_deg))
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def _to_time(t: float, time_type: Any) -> Any:
    sec = int(t)
    nanosec = int((t - sec) * 1_000_000_000)
    return time_type(sec=sec, nanosec=nanosec)


def export_dataset_to_bag(dataset_dir: Path, bag_dir: Path, overwrite: bool = False) -> Path:
    try:
        from rosbags.rosbag2 import Writer
        from rosbags.typesys import Stores, get_typestore
    except ImportError as exc:  # pragma: no cover - depends on environment packages
        raise RuntimeError(
            "rosbags is required for bag export. Install with: pip install 'hitresearch-sim[ros]'"
        ) from exc

    if bag_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"{bag_dir} already exists. Use --overwrite or choose a different --bag-dir."
            )
        shutil.rmtree(bag_dir)
    bag_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(dataset_dir / "dataset.csv").sort_values("frame_idx")
    if df.empty:
        raise ValueError(f"No frames found in {dataset_dir / 'dataset.csv'}")

    typestore = get_typestore(Stores.ROS2_HUMBLE)
    Time = typestore.types["builtin_interfaces/msg/Time"]
    Header = typestore.types["std_msgs/msg/Header"]
    Vector3 = typestore.types["geometry_msgs/msg/Vector3"]
    Point = typestore.types["geometry_msgs/msg/Point"]
    Quaternion = typestore.types["geometry_msgs/msg/Quaternion"]
    Pose = typestore.types["geometry_msgs/msg/Pose"]
    PoseStamped = typestore.types["geometry_msgs/msg/PoseStamped"]
    Imu = typestore.types["sensor_msgs/msg/Imu"]
    PathMsg = typestore.types["nav_msgs/msg/Path"]

    with Writer(str(bag_dir)) as writer:
        imu_conn = writer.add_connection("/imu/data", "sensor_msgs/msg/Imu", typestore=typestore)
        pose_conn = writer.add_connection(
            "/hitresearch/pose", "geometry_msgs/msg/PoseStamped", typestore=typestore
        )
        path_conn = writer.add_connection("/hitresearch/path", "nav_msgs/msg/Path", typestore=typestore)

        path_poses: list[Any] = []
        for row in df.itertuples(index=False):
            t = float(row.t)
            stamp = _to_time(t, Time)
            ts_ns = int(t * 1_000_000_000)

            qz, qw = _yaw_to_quaternion(float(row.yaw_deg))
            header = Header(stamp=stamp, frame_id="map")
            base_header = Header(stamp=stamp, frame_id="base_link")

            pose = Pose(
                position=Point(x=float(row.x), y=float(row.y), z=float(row.z)),
                orientation=Quaternion(x=0.0, y=0.0, z=qz, w=qw),
            )
            pose_msg = PoseStamped(header=header, pose=pose)
            path_poses.append(pose_msg)

            imu_msg = Imu(
                header=base_header,
                orientation=Quaternion(x=0.0, y=0.0, z=qz, w=qw),
                orientation_covariance=[-1.0] * 9,
                angular_velocity=Vector3(
                    x=float(row.imu_gx), y=float(row.imu_gy), z=float(row.imu_gz)
                ),
                angular_velocity_covariance=[0.0] * 9,
                linear_acceleration=Vector3(
                    x=float(row.imu_ax), y=float(row.imu_ay), z=float(row.imu_az)
                ),
                linear_acceleration_covariance=[0.0] * 9,
            )

            path_msg = PathMsg(header=header, poses=list(path_poses))
            writer.write(
                imu_conn, ts_ns, typestore.serialize_cdr(imu_msg, "sensor_msgs/msg/Imu")
            )
            writer.write(
                pose_conn,
                ts_ns,
                typestore.serialize_cdr(pose_msg, "geometry_msgs/msg/PoseStamped"),
            )
            writer.write(
                path_conn,
                ts_ns,
                typestore.serialize_cdr(path_msg, "nav_msgs/msg/Path"),
            )

    return bag_dir


def main() -> None:
    args = parse_args()
    run_dir: Path
    if args.dataset_dir is not None:
        run_dir = args.dataset_dir
    else:
        from hitresearch_sim.config.loader import load_config
        from hitresearch_sim.core.pipeline import SimulationPipeline

        cfg = load_config(args.config)
        pipeline = SimulationPipeline(cfg)
        run_dir = pipeline.run(args.run_idx)

    bag_dir = args.bag_dir or (run_dir / "rviz_demo_bag")
    out = export_dataset_to_bag(run_dir, bag_dir, overwrite=args.overwrite)
    print(f"dataset source: {run_dir}")
    print(f"rosbag2 written to: {out}")
    print("Use with ROS 2: ros2 bag play <bag_dir>, then open RViz to view /hitresearch/path and /hitresearch/pose")


if __name__ == "__main__":
    main()
