"""Fusion planner tests."""

from __future__ import annotations

from karakuri.robot.detections import BoundingBox, Detection, DetectionFrame
from karakuri.robot.planner import plan_frame
from karakuri.robot.validate import validate_plan


def _frame(detections):
    return DetectionFrame(detections=detections)


def test_toy_routes_to_pick_and_place():
    frame = _frame(
        [
            Detection("toy", 0.9, BoundingBox(100, 100, 50, 50), world=(300.0, 250.0, 20.0)),
            Detection("toy_box", 0.95, BoundingBox(600, 600, 100, 100), world=(700.0, 700.0, 0.0)),
        ]
    )
    result = plan_frame(frame)
    # pick + place + final retreat
    assert result.pick_step_count == 3
    assert result.place_target_found is True
    actions = [s["action"] for s in result.pick_plan["steps"]]
    assert actions == ["pick", "place", "retreat"]


def test_foam_routes_to_vacuum():
    frame = _frame([Detection("foam_bit", 0.8, BoundingBox(10, 10, 5, 5), world=(100.0, 100.0, 0.0))])
    result = plan_frame(frame)
    assert result.vacuum_waypoint_count == 1
    assert result.pick_step_count == 0
    assert "foam_bit" in result.vacuum_plan["target_classes"]


def test_large_trash_picks_small_trash_vacuums():
    big = Detection("trash", 0.8, BoundingBox(0, 0, 80, 80), world=(200.0, 200.0, 10.0))
    small = Detection("trash", 0.8, BoundingBox(0, 0, 10, 10), world=(300.0, 300.0, 10.0))
    result = plan_frame(_frame([big, small]))
    # big trash -> pick + place, plus final retreat = 3 pick steps
    assert result.pick_step_count == 3
    # small trash -> vacuum waypoint
    assert result.vacuum_waypoint_count == 1


def test_out_of_bounds_detection_skipped():
    frame = _frame([Detection("toy", 0.9, BoundingBox(0, 0, 10, 10), world=(5000.0, 0.0, 0.0))])
    result = plan_frame(frame)
    assert result.pick_step_count == 0
    assert any("out of bounds" in s.reason for s in result.skipped)


def test_unknown_class_skipped():
    frame = _frame([Detection("banana", 0.9, BoundingBox(0, 0, 10, 10), world=(100.0, 100.0, 0.0))])
    result = plan_frame(frame)
    assert any("not in shikai config" in s.reason for s in result.skipped)


def test_floor_is_ignored_not_skipped():
    frame = _frame([Detection("floor", 0.99, BoundingBox(0, 0, 10, 10), world=(100.0, 100.0, 0.0))])
    result = plan_frame(frame)
    assert result.is_empty
    assert result.skipped == []


def test_confidence_threshold_filters():
    frame = _frame(
        [
            Detection("foam_bit", 0.30, BoundingBox(0, 0, 5, 5), world=(100.0, 100.0, 0.0)),
            Detection("foam_bit", 0.90, BoundingBox(0, 0, 5, 5), world=(120.0, 100.0, 0.0)),
        ]
    )
    result = plan_frame(frame, confidence_threshold=0.5)
    assert result.vacuum_waypoint_count == 1


def test_generated_plans_validate_against_schemas():
    frame = _frame(
        [
            Detection("toy", 0.9, BoundingBox(100, 100, 50, 50), world=(300.0, 250.0, 20.0)),
            Detection("toy_box", 0.95, BoundingBox(600, 600, 100, 100), world=(700.0, 700.0, 0.0)),
            Detection("foam_bit", 0.8, BoundingBox(10, 10, 5, 5), world=(100.0, 100.0, 0.0)),
        ]
    )
    result = plan_frame(frame, mission_id="t")
    ok_pick, errors_pick = validate_plan("musubi", result.pick_plan)
    ok_vac, errors_vac = validate_plan("hane", result.vacuum_plan)
    assert ok_pick, errors_pick
    assert ok_vac, errors_vac


def test_plan_result_to_dict():
    frame = _frame([Detection("toy", 0.9, BoundingBox(0, 0, 10, 10), world=(100.0, 100.0, 0.0))])
    data = plan_frame(frame).to_dict()
    assert "pick_plan" in data
    assert "vacuum_plan" in data
    assert "skipped" in data
