"""Mission validation tests against the shipped subsystem schemas."""

from __future__ import annotations

from karakuri.robot.validate import validate_all_examples, validate_example, validate_plan


def test_shipped_examples_are_valid():
    results = validate_all_examples()
    for subsystem, (ok, errors) in results.items():
        assert ok, f"{subsystem} example invalid: {errors}"


def test_validate_example_musubi():
    ok, errors = validate_example("musubi")
    assert ok, errors


def test_validate_example_hane():
    ok, errors = validate_example("hane")
    assert ok, errors


def test_invalid_pick_plan_rejected():
    bad = {"mission_id": "x", "steps": []}  # min_items 1 violated
    ok, errors = validate_plan("musubi", bad)
    assert not ok
    assert any("at least 1" in e for e in errors)


def test_pick_plan_bad_enum_rejected():
    bad = {
        "mission_id": "x",
        "steps": [{"step_id": "s1", "object_class": "banana", "action": "pick"}],
    }
    ok, errors = validate_plan("musubi", bad)
    assert not ok
    assert any("not in" in e for e in errors)


def test_vacuum_plan_requires_waypoints():
    bad = {"mission_id": "x", "target_classes": ["foam_bit"], "waypoints": []}
    ok, errors = validate_plan("hane", bad)
    assert not ok


def test_vacuum_plan_valid_minimal():
    good = {
        "mission_id": "x",
        "target_classes": ["foam_bit"],
        "waypoints": [{"waypoint_id": "wp1", "x": 0.1, "y": 0.2}],
    }
    ok, errors = validate_plan("hane", good)
    assert ok, errors
