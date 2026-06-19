"""HAL mock and Phase 7 generator tests."""

from __future__ import annotations

import yaml

from karakuri.hardware import HAL
from karakuri.memory.failures import log_failure
from karakuri.robot.cliff import CliffConfig, CliffGuard


def test_hal_mock_flat_floor_is_safe():
    hal = HAL.mock()
    cfg = CliffConfig(
        sensor_ids=list(hal.cliffs.readings),
        mount_height_mm=35.0,
        trigger_distance_mm=60.0,
        poll_hz=50.0,
        max_speed_near_unknown_m_s=0.15,
    )
    assert CliffGuard(cfg).evaluate(hal.cliffs.readings).safe


def test_hal_emergency_stop_kills_everything():
    hal = HAL.mock()
    hal.motors.set_speeds(0.4, 0.4)
    hal.vacuum_relay.set(True)
    hal.motor_relay.set(True)
    hal.emergency_stop()
    assert hal.motors.left == 0.0
    assert hal.motors.right == 0.0
    assert hal.vacuum_relay.on is False
    assert hal.motor_relay.on is False


def test_servo_bank_round_trip():
    hal = HAL.mock()
    hal.servos.set_angle(15, 1.57)
    assert hal.servos.angles[15] == 1.57


def test_generator_drafts_from_failures(tmp_path, monkeypatch):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    from karakuri.promotion.generator import scan_and_draft

    failures = tmp_path / "failures.jsonl"
    for _ in range(3):
        log_failure("pick", "toy", "grasp slipped", path=failures)
    log_failure("vacuum", "foam_bit", "missed", path=failures)

    drafted = scan_and_draft(threshold=3, failures_path=failures)
    assert len(drafted) == 1
    playbook = yaml.safe_load(drafted[0].read_text(encoding="utf-8"))
    assert playbook["name"] == "fix_pick_toy"
    assert playbook["origin"] == "auto_generated"
    assert playbook["safety"]["max_joint_velocity_rad_s"] <= 0.5
    # Companion test file exists beside it
    assert (drafted[0].parent / "test_fix_pick_toy.py").is_file()
    # Queued for the normal promotion gate
    queue = (tmp_path / "memory" / "promotion_queue.json").read_text(encoding="utf-8")
    assert "fix_pick_toy.yaml" in queue


def test_generator_below_threshold_drafts_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("KARAKURI_ROOT", str(tmp_path))
    from karakuri.promotion.generator import scan_and_draft

    failures = tmp_path / "failures.jsonl"
    log_failure("pick", "toy", "slip", path=failures)
    assert scan_and_draft(threshold=3, failures_path=failures) == []
