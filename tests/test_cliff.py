"""ASHI cliff guard tests: the robot must never go down the stairs."""

from __future__ import annotations

import pytest

from karakuri.robot.cliff import CliffConfig, CliffGuard, load_cliff_config
from karakuri.stop import clear, is_stopped

_CONFIG = CliffConfig(
    sensor_ids=["cliff_front_left", "cliff_front_right", "cliff_rear_left", "cliff_rear_right"],
    mount_height_mm=35.0,
    trigger_distance_mm=60.0,
    poll_hz=50.0,
    max_speed_near_unknown_m_s=0.15,
)

_FLAT_FLOOR = {
    "cliff_front_left": 35.0,
    "cliff_front_right": 36.0,
    "cliff_rear_left": 35.0,
    "cliff_rear_right": 34.0,
}


def test_flat_floor_is_safe():
    status = CliffGuard(_CONFIG).evaluate(_FLAT_FLOOR)
    assert status.safe
    assert status.reason == "clear"


def test_stair_edge_triggers():
    # Approaching the top of a staircase: front sensors suddenly see the
    # next tread far below while the rear sensors still see floor.
    readings = dict(_FLAT_FLOOR)
    readings["cliff_front_left"] = 220.0
    readings["cliff_front_right"] = 215.0
    status = CliffGuard(_CONFIG).evaluate(readings)
    assert not status.safe
    assert "cliff_front_left" in status.triggered
    assert "cliff_front_right" in status.triggered


def test_reversing_toward_stairs_triggers():
    readings = dict(_FLAT_FLOOR)
    readings["cliff_rear_right"] = 300.0
    status = CliffGuard(_CONFIG).evaluate(readings)
    assert not status.safe
    assert status.triggered == ["cliff_rear_right"]


def test_single_corner_drop_is_enough():
    # Even one sensor over the edge means stop. No averaging.
    readings = dict(_FLAT_FLOOR)
    readings["cliff_front_left"] = 61.0
    status = CliffGuard(_CONFIG).evaluate(readings)
    assert not status.safe


def test_reading_at_threshold_is_safe():
    readings = dict(_FLAT_FLOOR)
    readings["cliff_front_left"] = 60.0
    assert CliffGuard(_CONFIG).evaluate(readings).safe


def test_missing_sensor_is_unsafe():
    # A dead sensor at the top of the stairs must count as danger.
    readings = dict(_FLAT_FLOOR)
    del readings["cliff_front_right"]
    status = CliffGuard(_CONFIG).evaluate(readings)
    assert not status.safe
    assert "cliff_front_right" in status.missing


def test_garbage_reading_is_unsafe():
    readings = dict(_FLAT_FLOOR)
    readings["cliff_front_left"] = -5.0
    assert not CliffGuard(_CONFIG).evaluate(readings).safe
    readings["cliff_front_left"] = 99999.0
    assert not CliffGuard(_CONFIG).evaluate(readings).safe


def test_check_and_stop_engages_kill_switch():
    clear()
    readings = dict(_FLAT_FLOOR)
    readings["cliff_front_left"] = 500.0
    status = CliffGuard(_CONFIG).check_and_stop(readings)
    assert not status.safe
    assert is_stopped()
    clear()


def test_check_and_stop_leaves_flag_clear_when_safe():
    clear()
    CliffGuard(_CONFIG).check_and_stop(_FLAT_FLOOR)
    assert not is_stopped()


def test_load_cliff_config_from_yaml():
    config = load_cliff_config()
    assert len(config.sensor_ids) == 4
    assert config.trigger_distance_mm == 60.0
    assert config.mount_height_mm == 35.0
    assert "cliff_front_left" in config.sensor_ids


def test_load_cliff_config_rejects_empty(tmp_path):
    import yaml

    for name, filename, payload in [
        ("shikai", "config.yaml", {"subsystem": "shikai", "classes": [], "ignore_classes": []}),
        ("musubi", "pick_plan.yaml", {"subsystem": "musubi"}),
        ("hane", "vacuum_plan.yaml", {"subsystem": "hane"}),
        ("ashi", "mobility.yaml", {"subsystem": "ashi", "cliff": {"sensors": []}}),
        ("karada", "body.yaml", {"subsystem": "karada"}),
    ]:
        d = tmp_path / name
        d.mkdir()
        (d / filename).write_text(yaml.safe_dump(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="no cliff sensors"):
        load_cliff_config(root=tmp_path)
