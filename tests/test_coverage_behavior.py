"""Coverage behavior state machine tests."""

from __future__ import annotations

import random

from karakuri.robot.coverage import (
    BACKUP,
    HALTED,
    SPIRAL,
    STRAIGHT,
    TURN,
    CoverageBehavior,
    CoverageParams,
)


def _behavior() -> CoverageBehavior:
    return CoverageBehavior(CoverageParams(), rng=random.Random(7))


def test_starts_in_spiral_with_decaying_turn():
    b = _behavior()
    first = b.step(0.1)
    later = b.step(2.0)
    assert first.state == SPIRAL
    assert later.w_rad_s < first.w_rad_s


def test_spiral_eventually_goes_straight():
    b = _behavior()
    for _ in range(400):
        cmd = b.step(0.1)
        if cmd.state == STRAIGHT:
            break
    assert cmd.state == STRAIGHT
    assert cmd.w_rad_s == 0.0


def test_bumper_triggers_backup_then_turn_then_straight():
    b = _behavior()
    b.step(60.0)  # well past the spiral
    cmd = b.step(0.1, bumper=True)
    assert cmd.state == BACKUP
    states = set()
    for _ in range(200):
        cmd = b.step(0.1)
        states.add(cmd.state)
        if cmd.state == STRAIGHT:
            break
    assert TURN in states
    assert cmd.state == STRAIGHT


def test_backup_reverses():
    b = _behavior()
    b.step(60.0)
    b.step(0.1, bumper=True)
    cmd = b.step(0.1)
    assert cmd.state == BACKUP
    assert cmd.v_m_s < 0


def test_cliff_overrides_everything():
    b = _behavior()
    b.step(60.0)
    cmd = b.step(0.1, cliff_safe=False)
    assert cmd.state == BACKUP
    assert cmd.v_m_s == 0.0


def test_halt_is_terminal():
    b = _behavior()
    b.halt()
    assert b.step(0.1).state == HALTED
    assert b.step(0.1, bumper=True).state == HALTED
