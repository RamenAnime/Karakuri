"""Arm IK and continuous wrist tests."""

from __future__ import annotations

import math

from karakuri.robot.arm import (
    ArmGeometry,
    forward_arm,
    normalize_roll,
    solve_arm_ik,
)
from karakuri.robot.safety import SafetyEnvelope

_ENV = SafetyEnvelope(
    max_joint_velocity_rad_s=0.5,
    x_bounds_mm=(0.0, 800.0),
    y_bounds_mm=(0.0, 800.0),
    z_bounds_mm=(0.0, 400.0),
    require_estop_gpio=False,
)


def test_ik_fk_roundtrip():
    target = (180.0, 60.0, 120.0)
    sol = solve_arm_ik(*target, envelope=_ENV)
    assert sol is not None
    fx, fy, fz = forward_arm(sol)
    assert math.isclose(fx, target[0], abs_tol=1e-6)
    assert math.isclose(fy, target[1], abs_tol=1e-6)
    assert math.isclose(fz, target[2], abs_tol=1e-6)


def test_out_of_envelope_rejected():
    assert solve_arm_ik(900.0, 0.0, 100.0, envelope=_ENV) is None


def test_out_of_reach_rejected():
    geo = ArmGeometry()
    assert solve_arm_ik(geo.max_reach + 150, 10.0, geo.base_height_mm, envelope=_ENV) is None


def test_wrist_roll_is_continuous():
    # Any number of turns is legal; only the resolved angle matters.
    assert math.isclose(normalize_roll(0.0), 0.0)
    assert math.isclose(normalize_roll(2 * math.pi), 0.0, abs_tol=1e-12)
    assert math.isclose(normalize_roll(5 * math.pi), math.pi, abs_tol=1e-12)
    assert math.isclose(normalize_roll(-math.pi / 2), 1.5 * math.pi, abs_tol=1e-12)
    sol = solve_arm_ik(180.0, 0.0, 120.0, wrist_roll=7 * math.pi, envelope=_ENV)
    assert sol is not None
    assert 0.0 <= sol.wrist_roll < 2 * math.pi


def test_gripper_width_clamped():
    sol = solve_arm_ik(180.0, 0.0, 120.0, gripper_width_m=5.0, envelope=_ENV)
    assert sol is not None
    assert sol.gripper_width_m <= 0.07
