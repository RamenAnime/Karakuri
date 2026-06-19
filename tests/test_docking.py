"""Battery monitor and docking state machine tests."""

from __future__ import annotations

from karakuri.robot.docking import (
    ChargeConfig,
    ChargeMonitor,
    DockingController,
    DockState,
)

_CFG = ChargeConfig(empty_v=11.6, full_v=14.4, low_pct=25.0, resume_pct=95.0, charge_detect_v=13.8)


def test_percent_curve():
    m = ChargeMonitor(_CFG)
    assert m.percent(11.6) == 0.0
    assert m.percent(14.4) == 100.0
    assert 49.0 < m.percent(13.0) < 51.0
    assert m.percent(10.0) == 0.0
    assert m.percent(15.0) == 100.0


def test_low_and_full_thresholds():
    m = ChargeMonitor(_CFG)
    assert m.is_low(12.0)
    assert not m.is_low(13.5)
    assert m.is_full(14.35)
    assert not m.is_full(13.5)


def test_full_docking_journey():
    ctl = DockingController(ChargeMonitor(_CFG))
    assert ctl.update(13.5) == DockState.ACTIVE
    # Battery sags low during cleaning
    assert ctl.update(12.1) == DockState.RETURNING
    # Driving home, dock not seen yet
    assert ctl.update(12.1) == DockState.RETURNING
    # AprilTag spotted
    assert ctl.update(12.1, dock_visible=True) == DockState.ALIGNING
    # Shoe lands on the strips, charger voltage present
    assert ctl.update(12.1, dock_visible=True, contact_voltage=14.2) == DockState.CHARGING
    # Charging climbs
    assert ctl.update(13.2, contact_voltage=14.2) == DockState.CHARGING
    # Full: back to work
    assert ctl.update(14.35, contact_voltage=14.2) == DockState.ACTIVE


def test_losing_dock_during_alignment_falls_back():
    ctl = DockingController(ChargeMonitor(_CFG))
    ctl.state = DockState.ALIGNING
    assert ctl.update(12.1, dock_visible=False) == DockState.RETURNING


def test_contact_lost_while_charging_realigns():
    ctl = DockingController(ChargeMonitor(_CFG))
    ctl.state = DockState.CHARGING
    assert ctl.update(13.0, contact_voltage=0.0) == DockState.ALIGNING
