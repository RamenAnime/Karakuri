"""Robot mission config loader tests."""

from karakuri.paths import project_root, robot_dir, robot_subsystem_dir
from karakuri.robot import load_mission_config


def test_robot_paths():
    root = project_root()
    assert robot_dir() == root / "robot"
    assert robot_subsystem_dir("shikai") == root / "robot" / "shikai"


def test_load_mission_config_structure():
    mission = load_mission_config()
    assert mission["version"] >= 1
    assert set(mission["subsystems"]) == {"shikai", "musubi", "hane", "ashi", "karada"}
    assert set(mission["paths"]) == {"shikai", "musubi", "hane", "ashi", "karada"}


def test_shikai_yolo_classes():
    mission = load_mission_config()
    shikai = mission["subsystems"]["shikai"]
    assert shikai["subsystem"] == "shikai"
    names = [c["name"] for c in shikai["classes"]]
    assert names == [
        "toy",
        "toy_box",
        "foam_bit",
        "hair_clump",
        "trash",
        "floor",
    ]
    assert shikai["ignore_classes"] == ["floor"]


def test_musubi_pick_plan_schema():
    mission = load_mission_config()
    musubi = mission["subsystems"]["musubi"]
    assert musubi["subsystem"] == "musubi"
    schema = musubi["schema"]["pick_plan"]
    assert "steps" in schema["required"]
    example = musubi["example"]
    assert example["mission_id"] == "toys_to_box_001"
    assert example["steps"][0]["action"] == "pick"


def test_hane_vacuum_plan_schema():
    mission = load_mission_config()
    hane = mission["subsystems"]["hane"]
    assert hane["subsystem"] == "hane"
    schema = hane["schema"]["vacuum_plan"]
    assert "waypoints" in schema["required"]
    example = hane["example"]
    assert "foam_bit" in example["target_classes"]
    assert example["waypoints"][0]["object_class"] == "foam_bit"


def test_ros2_stubs_present():
    mission = load_mission_config()
    assert mission["subsystems"]["shikai"]["ros2"]["package"] == "shikai_perception"
    assert mission["subsystems"]["musubi"]["ros2"]["package"] == "musubi_manipulation"
    assert mission["subsystems"]["hane"]["ros2"]["package"] == "hane_vacuum"
    assert mission["subsystems"]["ashi"]["ros2"]["package"] == "ashi_mobility"
