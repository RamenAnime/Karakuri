"""IMU fusion, fall detection, and balance recovery tests."""

from __future__ import annotations

import math

from karakuri.robot.balance import BalanceController, BalanceSim, run_recovery
from karakuri.robot.imu import ComplementaryFilter, FallDetector, ImuSample, accel_angles
from karakuri.stop import clear, is_stopped

_LEVEL = ImuSample(0.0, 0.0, 1.0, 0.0, 0.0, 0.0)


def test_accel_angles_level_and_tilted():
    assert accel_angles(_LEVEL) == (0.0, 0.0)
    rolled = ImuSample(0.0, math.sin(math.radians(20)), math.cos(math.radians(20)), 0, 0, 0)
    roll, pitch = accel_angles(rolled)
    assert abs(roll - 20.0) < 0.1 and abs(pitch) < 0.1


def test_filter_tracks_gyro_then_corrects_to_gravity():
    f = ComplementaryFilter(alpha=0.98)
    # one second of pure 10 deg/s roll gyro at 100 Hz
    spin = ImuSample(0.0, 0.0, 1.0, 10.0, 0.0, 0.0)
    for _ in range(100):
        f.update(spin, 0.01)
    assert 3.5 < f.roll < 6.0  # integrated, steadily pulled back by the level accel reference
    # now hold still level: the accelerometer wins back the drift
    for _ in range(600):
        f.update(_LEVEL, 0.01)
    assert abs(f.roll) < 1.0


def test_filter_rejects_bad_alpha():
    import pytest

    with pytest.raises(ValueError):
        ComplementaryFilter(alpha=1.5)


def test_fall_detector_engages_stop():
    clear()
    fd = FallDetector(limit_deg=32.0)
    assert fd.check(10.0, -5.0)
    assert not is_stopped()
    assert not fd.check(0.0, 40.0)
    assert is_stopped()
    clear()


def test_balance_recovers_from_real_leans():
    for start in (4.0, 9.0, 15.0):
        ok, trace = run_recovery(start)
        assert ok, f"failed to recover from {start} deg, final {trace[-1]:.2f}"


def test_balance_declares_unrecoverable_honestly():
    ok, _ = run_recovery(25.0)
    assert not ok


def test_uncontrolled_pendulum_falls():
    sim = BalanceSim(angle_deg=5.0)
    for _ in range(200):
        sim.step(0.0, 0.01)
    assert abs(sim.angle_deg) > 30.0  # physics is real: no control means a fall


def test_joint_deltas_clamped_and_distributed():
    ctl = BalanceController()
    d = ctl.joint_deltas(roll=10.0, pitch=20.0, roll_rate=0.0, pitch_rate=0.0)
    assert abs(d["l_ankle_pitch"]) > abs(d["l_hip_pitch"])     # ankles lead
    assert d["l_ankle_roll"] >= -25.0                          # clamp respected
    assert d["waist_yaw"] == 0.0
