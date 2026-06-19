"""Quadruped leg IK and creep gait tests."""

from __future__ import annotations

import math

from karakuri.robot.gait import (
    LEG_ORDER,
    GaitConfig,
    LegGeometry,
    creep_cycle,
    forward_leg,
    solve_leg_ik,
)


def test_ik_fk_roundtrip():
    target = (120.0, 20.0, 60.0)
    angles = solve_leg_ik(*target)
    assert angles is not None
    fx, fy, fz = forward_leg(angles)
    assert math.isclose(fx, target[0], abs_tol=1e-6)
    assert math.isclose(fy, target[1], abs_tol=1e-6)
    assert math.isclose(fz, target[2], abs_tol=1e-6)


def test_unreachable_returns_none():
    geo = LegGeometry()
    assert solve_leg_ik(geo.max_reach + 200, 0, 0) is None
    assert solve_leg_ik(geo.coxa_mm, 0, 0) is None  # inside minimum annulus


def test_straight_down_stance():
    angles = solve_leg_ik(34.0 + 80.0, 0.0, 80.0)
    assert angles is not None
    assert math.isclose(angles.coxa, 0.0, abs_tol=1e-9)


def test_creep_cycle_structure():
    phases = creep_cycle()
    assert len(phases) == 4
    assert [p["swing_leg"] for p in phases] == LEG_ORDER
    for phase in phases:
        assert len(phase["stance_legs"]) == 3
        assert len(phase["swing_targets"]) == 3
        lift = phase["swing_targets"][0]
        plant = phase["swing_targets"][2]
        assert lift[2] < plant[2]  # lifted foot is higher (smaller z-down)


def test_creep_cycle_targets_all_reachable():
    for phase in creep_cycle():
        for target in phase["swing_targets"]:
            assert solve_leg_ik(*target) is not None


def test_creep_stride_conserved():
    config = GaitConfig(stride_mm=48.0)
    phases = creep_cycle(config)
    total_shift = sum(p["stance_shift_mm"] for p in phases)
    assert math.isclose(total_shift, config.stride_mm)


def test_impossible_gait_geometry_raises():
    tiny = LegGeometry(femur_mm=20.0, tibia_mm=20.0)
    try:
        creep_cycle(GaitConfig(), tiny)
        raised = False
    except ValueError:
        raised = True
    assert raised
