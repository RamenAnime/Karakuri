"""Joint bus, RT loop, and absolute encoder tests."""

from __future__ import annotations

import pytest

from karakuri.robot.bus import FLAG_SYNC, FRAME_SIZE, JointBus, JointFrame, decode, encode
from karakuri.robot.encoders import JointEncoder, counts_to_deg, tracking_error
from karakuri.robot.rt import LoopTimer


def test_frame_roundtrip():
    f = JointFrame(node=14, seq=999, pos_deg=123.45, vel_deg_s=-50.5)
    out = decode(encode(f))
    assert out is not None
    assert out.node == 14 and out.seq == 999
    assert abs(out.pos_deg - 123.45) < 0.01
    assert abs(out.vel_deg_s + 50.5) < 0.01


def test_corrupted_frame_rejected():
    raw = bytearray(encode(JointFrame(1, 1, 90.0, 0.0)))
    raw[3] ^= 0xFF
    assert decode(bytes(raw)) is None
    assert decode(b"short") is None


def test_bus_sync_broadcast_and_sequencing():
    bus = JointBus()
    for node in range(1, 24):
        bus.command(node, 10.0 * node % 90)
    bus.sync()
    frames = [decode(b) for b in bus.transport.drain()]
    assert len(frames) == 24 and all(f is not None for f in frames)
    assert frames[-1].flags & FLAG_SYNC
    assert all(f.seq == 0 for f in frames)
    bus.command(1, 5.0)
    assert decode(bus.transport.drain()[0]).seq == 1


def test_frame_size_fits_classic_can_fd():
    assert FRAME_SIZE <= 64  # one CAN-FD frame, with room to grow


def test_encoder_wrap_and_velocity():
    enc = JointEncoder()
    enc.update(4090, 0.01)                     # near top of range
    angle = enc.update(10, 0.01)               # crosses zero forward
    assert enc.turns == 1
    assert 359.0 < angle < 361.5
    assert enc.velocity_deg_s > 0


def test_encoder_zero_calibration():
    enc = JointEncoder()
    enc.update(2048, 0.01)                     # physically at 180 raw
    enc.set_zero_here()
    assert abs(enc.angle_deg) < 1e-9
    enc.update(2048 + 114, 0.01)               # ~10 degrees later
    assert abs(enc.angle_deg - counts_to_deg(114)) < 0.01


def test_tracking_error_catches_slipped_horn():
    assert tracking_error(45.0, 43.0)
    assert not tracking_error(45.0, 20.0)


def test_loop_timer_schedules_and_accounts():
    lt = LoopTimer(period_s=0.002)
    for _ in range(50):
        lt.wait()
    s = lt.stats
    assert s.iterations == 50
    assert 0.0005 < s.mean_period_s < 0.02    # generous: CI boxes jitter
    assert s.worst_jitter_s >= 0.0


def test_loop_timer_rejects_bad_period():
    with pytest.raises(ValueError):
        LoopTimer(0)
