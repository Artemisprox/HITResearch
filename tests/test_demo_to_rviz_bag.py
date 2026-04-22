from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_demo_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "demo_to_rviz_bag.py"
    spec = importlib.util.spec_from_file_location("demo_to_rviz_bag", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_yaw_to_quaternion_zero() -> None:
    module = _load_demo_module()
    qz, qw = module._yaw_to_quaternion(0.0)
    assert qz == 0.0
    assert qw == 1.0


def test_to_time_splits_sec_and_nanosec() -> None:
    module = _load_demo_module()

    class FakeTime:
        def __init__(self, sec: int, nanosec: int) -> None:
            self.sec = sec
            self.nanosec = nanosec

    stamp = module._to_time(1.25, FakeTime)
    assert stamp.sec == 1
    assert stamp.nanosec == 250_000_000


def test_export_dataset_passes_writer_version(tmp_path: Path, monkeypatch) -> None:
    module = _load_demo_module()

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    (dataset_dir / "dataset.csv").write_text(
        "frame_idx,t,x,y,z,yaw_deg,imu_ax,imu_ay,imu_az,imu_gx,imu_gy,imu_gz\n"
        "0,0.0,0,0,1,0,0,0,9.81,0,0,0\n",
        encoding="utf-8",
    )
    bag_dir = tmp_path / "bag"

    class FakeWriter:
        last_version = None

        def __init__(self, _: str, *, version: int) -> None:
            FakeWriter.last_version = version

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_connection(self, *_args, **_kwargs):
            return 1

        def write(self, *_args, **_kwargs):
            return None

    def _msg_class(_name: str):
        class _Msg:
            def __init__(self, **kwargs) -> None:
                self.__dict__.update(kwargs)

        return _Msg

    class FakeTypeStore:
        def __init__(self) -> None:
            self.types = {
                "builtin_interfaces/msg/Time": _msg_class("Time"),
                "std_msgs/msg/Header": _msg_class("Header"),
                "geometry_msgs/msg/Vector3": _msg_class("Vector3"),
                "geometry_msgs/msg/Point": _msg_class("Point"),
                "geometry_msgs/msg/Quaternion": _msg_class("Quaternion"),
                "geometry_msgs/msg/Pose": _msg_class("Pose"),
                "geometry_msgs/msg/PoseStamped": _msg_class("PoseStamped"),
                "sensor_msgs/msg/Imu": _msg_class("Imu"),
                "nav_msgs/msg/Path": _msg_class("Path"),
            }

        def serialize_cdr(self, _msg, _msg_type: str) -> bytes:
            return b"cdr"

    fake_typesys = types.ModuleType("rosbags.typesys")
    fake_typesys.Stores = types.SimpleNamespace(ROS2_HUMBLE="ros2_humble")
    fake_typesys.get_typestore = lambda _store: FakeTypeStore()
    fake_rosbag2 = types.ModuleType("rosbags.rosbag2")
    fake_rosbag2.Writer = FakeWriter
    fake_rosbags = types.ModuleType("rosbags")
    fake_rosbags.rosbag2 = fake_rosbag2
    fake_rosbags.typesys = fake_typesys

    monkeypatch.setitem(sys.modules, "rosbags", fake_rosbags)
    monkeypatch.setitem(sys.modules, "rosbags.rosbag2", fake_rosbag2)
    monkeypatch.setitem(sys.modules, "rosbags.typesys", fake_typesys)

    out = module.export_dataset_to_bag(dataset_dir, bag_dir, bag_version=9)
    assert out == bag_dir
    assert FakeWriter.last_version == 9


def test_export_dataset_auto_renames_if_target_exists(tmp_path: Path, monkeypatch) -> None:
    module = _load_demo_module()

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    (dataset_dir / "dataset.csv").write_text(
        "frame_idx,t,x,y,z,yaw_deg,imu_ax,imu_ay,imu_az,imu_gx,imu_gy,imu_gz\n"
        "0,0.0,0,0,1,0,0,0,9.81,0,0,0\n",
        encoding="utf-8",
    )
    bag_dir = tmp_path / "bag"
    bag_dir.mkdir()

    class FakeWriter:
        def __init__(self, _path: str, *, version: int) -> None:
            self.version = version

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def add_connection(self, *_args, **_kwargs):
            return 1

        def write(self, *_args, **_kwargs):
            return None

    def _msg_class(_name: str):
        class _Msg:
            def __init__(self, **kwargs) -> None:
                self.__dict__.update(kwargs)

        return _Msg

    class FakeTypeStore:
        def __init__(self) -> None:
            self.types = {
                "builtin_interfaces/msg/Time": _msg_class("Time"),
                "std_msgs/msg/Header": _msg_class("Header"),
                "geometry_msgs/msg/Vector3": _msg_class("Vector3"),
                "geometry_msgs/msg/Point": _msg_class("Point"),
                "geometry_msgs/msg/Quaternion": _msg_class("Quaternion"),
                "geometry_msgs/msg/Pose": _msg_class("Pose"),
                "geometry_msgs/msg/PoseStamped": _msg_class("PoseStamped"),
                "sensor_msgs/msg/Imu": _msg_class("Imu"),
                "nav_msgs/msg/Path": _msg_class("Path"),
            }

        def serialize_cdr(self, _msg, _msg_type: str) -> bytes:
            return b"cdr"

    fake_typesys = types.ModuleType("rosbags.typesys")
    fake_typesys.Stores = types.SimpleNamespace(ROS2_HUMBLE="ros2_humble")
    fake_typesys.get_typestore = lambda _store: FakeTypeStore()
    fake_rosbag2 = types.ModuleType("rosbags.rosbag2")
    fake_rosbag2.Writer = FakeWriter
    fake_rosbags = types.ModuleType("rosbags")
    fake_rosbags.rosbag2 = fake_rosbag2
    fake_rosbags.typesys = fake_typesys

    monkeypatch.setitem(sys.modules, "rosbags", fake_rosbags)
    monkeypatch.setitem(sys.modules, "rosbags.rosbag2", fake_rosbag2)
    monkeypatch.setitem(sys.modules, "rosbags.typesys", fake_typesys)

    out = module.export_dataset_to_bag(dataset_dir, bag_dir, overwrite=False)
    assert out != bag_dir
    assert out.name.startswith("bag_")
